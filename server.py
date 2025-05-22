from mcp.server.fastmcp import FastMCP
from tools.calculator import register_calculator_tools
from tools.iot import register_iot_tools


mcp = FastMCP("ServerMCP")

register_calculator_tools(mcp)
register_iot_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")

