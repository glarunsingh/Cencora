from langchain_openai import AzureChatOpenAI
model = AzureChatOpenAI(temperature=0.3,
                        openai_api_key="10a5c5995bd74909bfeb43de6c11c4bf",
                        openai_api_version="2024-02-15-preview",
                        azure_deployment="gpt-4o",
                        azure_endpoint = "https://qa.gai.cencora.com/aoai",
                        verbose=True)
from langchain_core.messages import HumanMessage
message = HumanMessage(
    content="Translate this sentence from English to French. I love programming."
)
print(model.invoke([message]))