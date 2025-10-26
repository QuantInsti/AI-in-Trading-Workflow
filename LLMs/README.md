# LLMs in Trading Workflows

**For Educational and Paper Trading Purposes Only**

The content, code, and strategies provided in this repository are for educational and informational purposes only. They are not intended as financial advice, investment recommendations, or a solicitation to buy or sell any securities.

**Trading financial markets involves substantial risk, and you are solely responsible for any decisions you make. The authors and contributors of this repository assume no liability for any financial losses you may incur.**

Always conduct your own thorough research and risk assessment before deploying any trading strategy in a live environment. You should start by using these examples with paper trading accounts.

---

This section provides examples of different architectural patterns for using Large Language Models (LLMs) in trading workflows. The examples demonstrate how to build agent-based systems that can perform analysis, make decisions, and execute trades.

### Architectural Approaches

*   **Client-Server Model:** This pattern involves a client application that communicates with a separate server responsible for handling LLM interactions.
*   **Agentic Frameworks (LangGraph):** This approach uses libraries like LangGraph to build complex, stateful multi-agent systems where different agents can collaborate on a task.

### Available Use Cases

The following examples are available in this directory:

[**Example 01: Create an IB MCP Server in Python**](./example_01_create_ib_mcp_server_in_python/README.md): This example demonstrates a client-server architecture. A Python client connects to Interactive Brokers (IB) and communicates with a Node.js "Multi-Content Prompt" (MCP) server that uses the Gemini API to generate trading signals.
[**Example 02: Agentic AI-based Portfolio Manager using Alpaca API**](./example_02_Agentic_AI_based_Portfolio_manager_using_Alpaca_API/README.md): An example of an autonomous, agentic portfolio manager built with LangGraph. This system performs news analysis, quantitative analysis, portfolio allocation, and trade execution with risk management via the Alpaca API.
