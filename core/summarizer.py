import os 

def get_llm():
    from langchain_openai import ChatOpenAI
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        return ChatOpenAI(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=0.3,
            max_retries=3,
        )
    if os.getenv("USE_OLLAMA", "").lower() == "true":
        return ChatOpenAI(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
            api_key="ollama",
            base_url="http://localhost:11434/v1",
            temperature=0.3,
        )
    model_name = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    api_key = os.getenv("OPENROUTER_API_KEY")
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.3,
        max_retries=3,
        request_timeout=90,
    )

def split_transcript(transcript: str) -> list:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )
    return splitter.split_text(transcript)

def summarize(transcript: str) -> str:
    import time
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda

    llm = get_llm()

    chunks = split_transcript(transcript)
    if not chunks:
        return "No transcript content available to summarize."

    # Single-chunk fast path: eliminates extra Map-Reduce API call
    if len(chunks) == 1:
        single_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert meeting summarizer. Provide a concise, professional "
                "meeting summary in bullet points based on the transcript.",
            ),
            ("human", "{text}"),
        ])
        single_chain = single_prompt | llm | StrOutputParser()
        return single_chain.invoke({"text": chunks[0]})

    map_prompt = ChatPromptTemplate.from_messages([
        ("system", "Summarize this portion of a meeting transcript concisely."),
        ("human", "{text}"),
    ])
    map_chain = map_prompt | llm | StrOutputParser()

    chunk_summaries = []
    for chunk in chunks:
        chunk_summaries.append(map_chain.invoke({"text": chunk}))
        time.sleep(1.5)

    combined = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting summarizer. Combine these partial summaries "
            "into one final professional meeting summary in bullet points.",
        ),
        ("human", "{text}"),
    ])

    combined_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x: {"text": x}) | combined_prompt | llm | StrOutputParser()
    )

    return combined_chain.invoke(combined)

def generate_title(transcipt : str) -> str:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda

    llm = get_llm()

    title_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x:{"text":x}) | 
        ChatPromptTemplate.from_messages([
             (
                "system",
                "Based on the meeting transcript, generate a short professional meeting title "
                "(max 8 words). Only return the title, nothing else.",
            ),
            ("human", "{text}"),
        ])
        | llm
        |StrOutputParser()
    )

    return title_chain.invoke(transcipt[:2000])