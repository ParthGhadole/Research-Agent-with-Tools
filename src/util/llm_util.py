import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from custom_azureopenai_langchain import get_azure_chat_openai
load_dotenv()

def get_llm(provider = "gemini", model = "gemini-2.5-flash-lite", temperature = -1):
        
    if provider == "gemini":    
        configs = {
            "gemini-2.5-flash-lite": 0.2,
            "gemini-2.5-flash": 0.5,
            "gemini-3-flash-preview": 0.5
        }
        if temperature==-1:
            temperature = configs.get(model, 0.5)

        return ChatGoogleGenerativeAI(
            model = model, 
            temperature = temperature, 
            verbose = True
        )
    elif provider == "azureopenai":
        if temperature!=-1 and temperature>0 and temperature<1:
            return get_azure_chat_openai(temperature = temperature, max_tokens = 2000)
        else:
            return get_azure_chat_openai(temperature = 0.5,max_tokens=2000)
        
    else:
        return ChatGoogleGenerativeAI(
                model = "gemini-2.5-flash-lite", 
                temperature = 0.2, 
                verbose = True
            )
        
def get_llm_with_tools(provider ,model, temperature, tools):
        
    if provider == "gemini":    
        configs = {
            "gemini-2.5-flash-lite": 0.2,
            "gemini-2.5-flash": 0.5,
            "gemini-3-flash-preview": 0.5
        }
        if temperature==-1:
            temperature = configs.get(model, 0.5)

        return ChatGoogleGenerativeAI(
            model = model, 
            temperature = temperature, 
            verbose = True
        ).bind_tools(tools=tools)
    elif provider == "azureopenai":
        if temperature!=-1 and temperature>0 and temperature<1:
            return get_llm(provider=provider,temperature=temperature).bind_tools(tools=tools)
        else:
            return get_llm(provider=provider,temperature = 0.5).bind_tools(tools=tools)
        
    return
