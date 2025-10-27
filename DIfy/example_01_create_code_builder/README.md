## How to Build a Trading Backtester Agent in Dify

**For Educational and Paper Trading Purposes Only**

The content, code, and strategies provided in this repository are for
educational and informational purposes only. They are not intended as
financial advice, investment recommendations, or a solicitation to buy
or sell any securities.

**Trading financial markets involves substantial risk, and you are
solely responsible for any decisions you make. The authors and
contributors of this repository assume no liability for any financial
losses you may incur.**

Always conduct your own thorough research and risk assessment before
deploying any trading strategy in a live environment. You should start
by using these examples with paper trading accounts.

This tutorial guides you through creating a multi-agent workflow in
[Dify](https://cloud.dify.ai/apps) designed to generate Python
backtesting scripts for trading strategies. The system uses a chain of
specialized AI agents to refine an idea into a complete, risk-managed
script.

The final workflow is as follows: Start -\> Strategist -\> Coder -\>
RiskCoder -\> Code -\> Answer

### Step 1: Create the chat 
1. Open [Dify](https://cloud.dify.ai/apps)
2. Go to "CREATE APP" and click on "Create from Blank".

![image01](res/image01.png)

3. Click on "Chatflow"
4. In "App Name & Icon", type (you can customize this as per your needs): "A Code Builder"
5. In "Description", write something like (or anything you would want): "A Code Builder to create strategy backtesting scripts".

![image02](res/image02.png)


### Step 1: The Start Node
This is the entry point for the application. It captures the user's initial trading idea.

1.  By default, a new application starts with a Start node and an ANSWER.

![image03](res/image03.png)

### Step 2: The Strategist Node

This agent's job is to take the user's raw idea and formulate a
structured trading plan.

1.  Move your cursor to the line that connects both the START and ANSWER rectangles and click on the "plus" button that inmediately appears in the middle of the line. Then, a new window will pop out, where in "Nodes", you will click on "LLM".

![image04](res/image04.gif)

2.  Rename the node to **Strategist** as follows:

![image05](res/image05.gif)

3.  **Model** **Selection**:

    -   Set the model of your choice. As of November 2025, we have chosen Gemini Pro 2.5. In the Strategist's Settings, go to MODEL, click on the down arrow on the right of the model. A new sub-window will pop out. At the top, click on the down arrow of the MODEL section. Next, click on the "Model Provider Settings". Then, choose your LLM provider of your preference. In this case, we choose GEMINI. In addition, we set the API Key by clicking on config. Then we "Add API Key". Finally you set a customized "Authorization Name" and then you set your Gemini "API key". Finally, you click on save. This will alow having an LLM for your Strategist.
	
![image06](res/image06.gif)

4.  **Prompt Configuration**:

    -   In the **SYSTEM PROMPT** section, insert the following text:

    ```
	You are an expert trading strategist. Create a trading plan based on the user's request.
    ```
	
![image07](res/image07.gif)

### Step 3: The Coder Node

This agent takes the trading plan from the Strategist and writes the
initial Python code.

1.  Move your cursor to the line that connects the Strategist and the ANSWER and click on the "+" button. Select the node "LLM".

![image08](res/image08.gif)

2.  Rename the node to **Coder**.

![image09](res/image09.gif)

3.  **Model Selection**:

    -   Set the model to the one of your choice as in Setep 2, point 3.

4.  **Prompt Configuration**:

    -   In the **SYSTEM PROMPT** section, insert the following:

    ```
    You are an expert Python programmer specializing in trading strategies. Generate Python code for the provided trading strategy located in 'Strategist / {x} text'.
    ```
![image10](res/image10.gif)

### Step 4: The RiskCoder Node

This agent enhances the generated code by adding risk management and
real-world trading considerations.

1.  Click the **+** icon in the line between the the Coder and ANSWER nodes and select **LLM**.

![image11](res/image11.gif)

2.  Rename the node to **RiskCoder**.

![image12](res/image12.gif)

3.  **Model Selection**:

    -   Set the model to Gemini 2.5 Pro as you did in the previous steps.

4.  **Prompt Configuration**:

    -   In the **SYSTEM PROMPT** section, insert the following:

    ```
    You are an expert Python programmer specializing in trading strategies. Use the Coder\'s Python code output located in 'Coder / {x} text' and improve it in such a way that you add risk management thresholds, transaction costs provided by the Alpaca brokerage and slippage.
    ``` 
![image13](res/image13.gif)

### Step 5: The Code Node

This node executes a Python snippet to structure the final output.

1.  Click the **+** icon in the line between the the RiskCoder and ANSWER nodes and select **Code**.

![image14](res/image14.gif)

2.  **Input Variables**:

    -   There are two default arg variables. Use the first one for the below instructions.

    -   Set the variable name to structured_code.

    -   For its value, select the output from the previous node:
        > RiskCoder / text.

	![image15](res/image15.gif)

    -   You can drop the second argument named "arg2" if desired.

3.  **Code Block**:

    -   In the Python 3 code editor, insert the following function:

    ```
	**def** main(structured_code: str) -\> dict:\
        > **return** {\
        > \"result\": structured_code,\
        > }
    ```


	![image16](res/image16.gif)

5.  **Output Variables**:

    -   The result variable is automatically detected from the return
        > statement.

### Step 6: The Answer Node

This is the final node that delivers the completed, risk-managed Python
script to the user.

1.  Select the Answer node.

2.  In the **Answer** settings, choose **{x}**.

3.  Select the output from the Code node: Code / result.

![image17](res/image17.gif)


The multi-agent trading script generator is now complete. When a user
provides a strategy idea, it will pass through this workflow to produce
a backtesting script.

*Note: This README provides a tutorial on how to build the multi-agent
system in Dify.* *To understand how the prompts were generated, please
refer to the how_to_build_a\_trading_backtester_agent_in_dify.md file.*

### Link to the multi-agent system Code Builder

Find below our Code Builder: https://udify.app/chat/ax5EIlxA2F0jTmCO

You can try the multi-agent system by prompting a basic example text to
describe your trading strategy. The system will take care of everything
and will create the code script for you. Just take into account that the
chat might not work due to LLM token limits.

### Next Steps and Experimentation

This project demonstrates a powerful low-code approach to building
agentic workflows. To deepen your understanding, we strongly recommend
the following activities:

-   **Tweak the Prompts:**

    -   Open the Dify visual editor and modify the system prompts for
        > the Strategist, Coder, or RiskCoder nodes. For example, make
        > the RiskCoder's instructions more specific about the *type* of
        > risk management to add (e.g., "always add a trailing stop-loss
        > of 2%").

-   **Extend the Project:**

    -   **Add a New Node:** This is an excellent way to learn about
        > chaining agents. Add a new LLM node to the Dify workflow. For
        > example, create a CodeReviewer agent that comes after the
        > RiskCoder. Its prompt could be: "You are a senior Python
        > developer. Review the following trading script for bugs, style
        > issues, or inefficiencies and add your comments at the top of
        > the script."

    -   **Experiment with Different Models:** Try swapping out the
        > Gemini Pro model for another model available in Dify to see
        > how it impacts the quality and style of the generated code.

This is a basic example on how to a create an agent
