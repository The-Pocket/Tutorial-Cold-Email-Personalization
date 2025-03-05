from pocketflow import Node, BatchNode, Flow
from utils.call_llm import call_llm
from utils.search_web import search_web
from utils.content_retrieval import get_html_content
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("personalization_flow")


class SearchPersonNode(Node):
    def prep(self, shared):
        # Read target person info from shared store
        first_name = shared["input"]["first_name"]
        last_name = shared["input"]["last_name"]
        keywords = shared["input"]["keywords"]
        
        # Format the search query
        query = f"{first_name} {last_name} {keywords}"
        logger.info(f"Prepared search query: '{query}'")
        return query
    
    def exec(self, query):
        # Execute web search
        logger.info(f"Executing web search with query: '{query}'")
        search_results = search_web(query)
        logger.debug(f"Search returned {len(search_results)} results")
        return search_results
    
    def post(self, shared, prep_res, exec_res):
        # Store search results in shared store
        shared["search_results"] = exec_res
        logger.info(f"Stored {len(exec_res)} search results in shared store")
        return "default"


class ContentRetrievalNode(BatchNode):
    def prep(self, shared):
        # Get list of URLs from search results
        search_results = shared["search_results"]
        urls = [result["link"] for result in search_results if "link" in result]
        logger.info(f"Preparing to retrieve content from {len(urls)} URLs")
        return urls
    
    def exec(self, url):
        # Retrieve content from URL
        logger.debug(f"Retrieving content from URL: {url}")
        content = get_html_content(url)
        return {"url": url, "content": content}
    
    def exec_fallback(self, prep_res, exc):
        # This is called after all retries are exhausted
        url = prep_res["url"]  # Extract URL from the prep_res input pair
        logger.error(f"Failed to retrieve content from {url} after all retries: {exc}")
        return {"url": url, "content": None}
    
    def post(self, shared, prep_res, exec_res_list):
        # Store only non-empty webpage contents
        valid_contents = [res for res in exec_res_list if res["content"]]
        shared["web_contents"] = valid_contents
        logger.info(f"Retrieved content from {len(valid_contents)}/{len(exec_res_list)} URLs successfully")
        return "default"


class AnalyzeResultsBatchNode(BatchNode):
    def prep(self, shared):
        # Store first_name, last_name, and personalization_factors for exec
        self.first_name = shared["input"]["first_name"]
        self.last_name = shared["input"]["last_name"]
        self.personalization_factors = shared["input"]["personalization_factors"]
        
        # Return list of (url, content) pairs
        url_content_pairs = list(shared["web_contents"])
        logger.info(f"Analyzing content from {len(url_content_pairs)} web pages")
        return url_content_pairs
    
    def exec(self, url_content_pair):
        url, content = url_content_pair["url"], url_content_pair["content"]
        logger.debug(f"Analyzing content from: {url}")
        
        # Prepare prompt for LLM analysis
        prompt = f"""Analyze the following webpage content about {self.first_name} {self.last_name}.
Look for the following personalization factors:
{self._format_personalization_factors(self.personalization_factors)}

Content from {url}:
Title: {content["title"]}

Text:
{content["text"]}  # Limit text to avoid overly large prompts

For each factor, return if you found relevant information and details.
Format your response as YAML:
```yaml
factors:
    - name: "factor_name"
    action: "action to take"
    actionable: true/false
    details: "supporting details if actionable"
    - name: "another_factor"
    action: "action to take"
    actionable: true/false
    details: "supporting details if actionable"
```"""
        
        # Call LLM to analyze the content
        logger.debug(f"Calling LLM to analyze content from {url}")
        response = call_llm(prompt)
        
        # Extract YAML portion from the response
        import yaml
        yaml_part = response.split("```yaml")[1].split("```")[0].strip()
        analysis = yaml.safe_load(yaml_part)
        logger.debug(f"Successfully parsed YAML from LLM response for {url}")
        return {"url": url, "analysis": analysis}
    
    def exec_fallback(self, prep_res, exc):
        # This is called after all retries are exhausted
        url = prep_res["url"]  # Extract URL from the prep_res input pair
        logger.error(f"Failed to analyze content from {url} after all retries: {exc}")
        return {"url": url, "analysis": {"factors": []}}
    
    def _format_personalization_factors(self, factors):
        formatted = ""
        for i, factor in enumerate(factors):
            formatted += f"{i+1}. {factor['name']}: {factor['description']}\n   Action: {factor['action']}\n"
        return formatted
    
    def post(self, shared, prep_res, exec_res_list):
        # Initialize personalization in shared store
        shared["personalization"] = {}
        
        # Process all analysis results
        found_factors = 0
        total_factors = 0
        
        # Dictionary to temporarily store details for each factor across sources
        factor_details = {}
        
        for result in exec_res_list:
            if "analysis" in result and "factors" in result["analysis"]:
                for factor in result["analysis"]["factors"]:
                    total_factors += 1
                    if factor.get("actionable", False):
                        found_factors += 1
                        factor_name = factor["name"]
                        
                        # Initialize if first time seeing this factor
                        if factor_name not in factor_details:
                            factor_details[factor_name] = []
                        
                        # Add details from this source
                        factor_details[factor_name].append(factor["details"])
        
        # Process collected details and create final personalization entries
        for factor_name, details_list in factor_details.items():
            # Find the matching factor from input to get the action
            for input_factor in shared["input"]["personalization_factors"]:
                if input_factor["name"] == factor_name:
                    # Merge all details for this factor
                    merged_details = " | ".join(details_list)
                    
                    shared["personalization"][factor_name] = {
                        "actionable": True,
                        "details": merged_details,
                        "action": input_factor["action"]
                    }
                    logger.debug(f"Found information for factor: {factor_name}")
                    break
        
        logger.info(f"Analysis complete: Found information for {found_factors}/{total_factors} factors across {len(exec_res_list)} sources")
        return "default"


class DraftOpeningNode(Node):
    def prep(self, shared):
        # Gather all necessary information
        person_info = {
            "first_name": shared["input"]["first_name"],
            "last_name": shared["input"]["last_name"]
        }
        
        personalization = shared["personalization"]
        style = shared["input"]["style"]
        
        logger.info(f"Preparing to draft opening message for {person_info['first_name']} {person_info['last_name']}")
        logger.debug(f"Found {len(personalization)} personalization factors to include")
        return person_info, personalization, style
    
    def exec(self, prep_data):
        person_info, personalization, style = prep_data
        
        # Prepare prompt for LLM
        prompt = f"""Generate a personalized opening message for a cold outreach email to {person_info["first_name"]} {person_info["last_name"]}.

Based on our research, we found the following personalization factors:
{self._format_personalization_details(personalization)}

Style preferences: {style}

Write a concise opening paragraph (1-3 sentences) that:
1. Addresses the person by first name
2. Includes the personalization points we found
3. Matches the requested style
4. Feels authentic and not forced

Only return the opening message, nothing else."""
        
        # Call LLM to draft the opening
        logger.debug("Calling LLM to draft personalized opening message")
        return call_llm(prompt)
    
    def _format_personalization_details(self, personalization):
        if not personalization:
            return "No specific personalization factors were actionable."
        
        formatted = ""
        for factor_name, details in personalization.items():
            formatted += f"- {factor_name}: {details['details']}\n  Action: {details['action']}\n"
        return formatted
    
    def post(self, shared, prep_res, exec_res):
        # Store the opening message in the output
        if "output" not in shared:
            shared["output"] = {}
        shared["output"]["opening_message"] = exec_res
        logger.info("Successfully generated and stored personalized opening message")
        return "default"


# Create nodes
logger.info("Initializing flow nodes")
search_node = SearchPersonNode()
content_node = ContentRetrievalNode()
analyze_node = AnalyzeResultsBatchNode(max_retries=2, wait=10)  # Retry up to 3 times before using fallback
draft_node = DraftOpeningNode(max_retries=3, wait=10)

# Connect nodes in the flow
logger.info("Connecting nodes in personalization flow")
search_node >> content_node >> analyze_node >> draft_node

# Create the flow
cold_outreach_flow = Flow(start=search_node)
logger.info("Personalization flow initialized successfully")