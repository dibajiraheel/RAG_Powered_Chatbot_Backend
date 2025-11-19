from langchain_tavily import TavilySearch
from dotenv import load_dotenv


load_dotenv()

tavily_search = TavilySearch(max_results = 3, search_depth = 'basic')

available_tools = [tavily_search]
tools_dict = {}
for available_tool in available_tools:
    tools_dict[available_tool.name] = available_tool
