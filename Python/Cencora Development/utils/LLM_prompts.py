from langchain_core.prompts import PromptTemplate

stuff_template = """Write a concise summary of the following:


"{text}"


CONCISE SUMMARY:"""
Stuff_prompt = PromptTemplate(template=stuff_template, input_variables=["text"])