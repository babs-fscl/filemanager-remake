import nest_asyncio, sys
import pydantic
if pydantic.__version__.startswith('2'):
    from pydantic import v1 as pydantic_v1
    sys.modules['langchain_core.pydantic_v1'] = pydantic_v1
    sys.modules['pydantic.v1'] = pydantic_v1
else:
    sys.modules['langchain_core.pydantic_v1'] = pydantic

# Handle missing langchain modules by redirecting to langchain_classic if available
try:
    import langchain.chains
except ImportError:
    try:
        import langchain_classic.chains
        sys.modules['langchain.chains'] = langchain_classic.chains
    except ImportError:
        pass

try:
    import langchain.text_splitter
except ImportError:
    try:
        import langchain_classic.text_splitter
        sys.modules['langchain.text_splitter'] = langchain_classic.text_splitter
    except ImportError:
        pass
from django.conf import settings
from .models import Project, Document as Dokument

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

nest_asyncio.apply()

_chat_model = None


def get_rag_dependencies():
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_mistralai.chat_models import ChatMistralAI
        from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        try:
            from langchain.chains.combine_documents import create_stuff_documents_chain
        except ImportError:
            from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
            
        from langchain_core.prompts import ChatPromptTemplate
        
        try:
            from langchain.chains import create_retrieval_chain
        except ImportError:
            from langchain.chains.retrieval import create_retrieval_chain
    except ImportError as exc:
        raise ValueError(f"LangChain RAG dependencies are not available: {exc}") from exc

    return (
        Chroma,
        ChatMistralAI,
        SentenceTransformerEmbeddings,
        RecursiveCharacterTextSplitter,
        create_stuff_documents_chain,
        ChatPromptTemplate,
        create_retrieval_chain,
    )


def get_legacy_chain_dependencies():
    try:
        try:
            from langchain.chains import ConversationalRetrievalChain, LLMChain
        except ImportError:
            from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
            from langchain.chains.llm import LLMChain
            
        from langchain.chains.question_answering import load_qa_chain
        from langchain.memory import ConversationBufferWindowMemory
    except ImportError as exc:
        raise ValueError(f"Legacy LangChain chain dependencies are not available: {exc}") from exc

    return ConversationalRetrievalChain, LLMChain, load_qa_chain, ConversationBufferWindowMemory


def get_chat_model():
    global _chat_model
    if not settings.MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY is not configured.")
    if _chat_model is None:
        _, ChatMistralAI, _, _, _, _, _ = get_rag_dependencies()
        _chat_model = ChatMistralAI(mistral_api_key=settings.MISTRAL_API_KEY)
    return _chat_model


def process_langchain_rag(doc_id, query, chat_history=None):
    (
        Chroma,
        _,
        SentenceTransformerEmbeddings,
        RecursiveCharacterTextSplitter,
        create_stuff_documents_chain,
        ChatPromptTemplate,
        create_retrieval_chain,
    ) = get_rag_dependencies()

    try:
        doc = Dokument.objects.get(pk=doc_id)
    except Dokument.DoesNotExist:
        raise ValueError(f"Document not found: {doc_id}")

    if not doc.content or not doc.content.strip():
        raise ValueError("This document has no extracted content yet. Please upload it again so its content can be loaded.")

    docs = [Document(page_content=doc.content, metadata={"source": f"project_{doc_id}"})]
    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(docs)
    import uuid
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # Use a unique collection to prevent mixing files and memory leaks
    collection_name = f"doc_{doc_id}_{uuid.uuid4().hex}"
    vector_store = Chroma.from_documents(documents, embedding_function, collection_name=collection_name)
    retriever = vector_store.as_retriever()
    model = get_chat_model()

    # Format chat history for the prompt
    history_text = ""
    history_list = list(chat_history or [])
    for msg in history_list[-6:]: # Keep last 3 turns (6 messages)
        role = "Human" if not msg.is_bot_response else "AI"
        history_text += f"{role}: {msg.message}\n"

    prompt = ChatPromptTemplate.from_template("""
    You are an AI assistant tasked with answering questions strictly based on the provided document context.
    You must provide accurate, clean, and comprehensive answers and explanations.

    IMPORTANT RULES:
    1. Rely strictly on the information provided in the context.
    2. If the context does not contain the answer, explicitly state "I cannot answer this based on the provided document." Do not hallucinate or use external general knowledge.
    3. Format your response cleanly using markdown (e.g. bolding, bullet points, headers) for readability.

    Here is the context you have:
    <context>
    {context}
    </context>

    Chat History:
    {chat_history}

    Question: {input}

    Answer:
    """)

    # Create a retrieval chain to answer questions
    document_chain = create_stuff_documents_chain(model, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    response = retrieval_chain.invoke({
        "input": query,
        "chat_history": history_text
    })

    # Clean up to avoid crossing files and memory bloat
    try:
        vector_store.delete_collection()
    except Exception:
        pass

    return response["answer"]


def process_langchain_rag_project(proj_id, query, chat_history=None):
    (
        Chroma,
        _,
        SentenceTransformerEmbeddings,
        RecursiveCharacterTextSplitter,
        create_stuff_documents_chain,
        ChatPromptTemplate,
        create_retrieval_chain,
    ) = get_rag_dependencies()

    try:
        proj = Project.objects.get(pk=proj_id)
    except Project.DoesNotExist:
        raise ValueError(f"Project not found: {proj_id}")

    if not proj.content or not proj.content.strip():
        raise ValueError("This project has no content yet. Please recreate the project so its content can be loaded.")

    docs = [Document(page_content=proj.content, metadata={"source": f"project_{proj_id}"})]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    documents = text_splitter.split_documents(docs)

    import uuid
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    collection_name = f"proj_{proj_id}_{uuid.uuid4().hex}"
    vector_store = Chroma.from_documents(documents, embedding_function, collection_name=collection_name)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    model = get_chat_model()

    # Format chat history for the prompt
    # Convert QuerySet to list because Django QuerySets don't support negative indexing
    history_text = ""
    history_list = list(chat_history or [])
    for msg in history_list[-6:]: # Keep last 3 turns (6 messages)
        role = "Human" if not msg.is_bot_response else "AI"
        history_text += f"{role}: {msg.message}\n"

    prompt = ChatPromptTemplate.from_template("""
    You are a helpful and knowledgeable AI assistant.
    Use the following pieces of context to answer the user's question in a detailed, comprehensive, and well-explained manner.
    When answering, break down complex concepts, provide examples if relevant, and ensure the explanation is thorough and easy to understand.
    If the context doesn't contain the exact answer, you may use your general knowledge to assist, but prioritize the provided document context.

    Context:
    {context}

    Chat History:
    {chat_history}

    Human: {input}
    AI: """)

    document_chain = create_stuff_documents_chain(model, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    response = retrieval_chain.invoke({
        "input": query,
        "chat_history": history_text
    })

    try:
        vector_store.delete_collection()
    except Exception:
        pass

    return response["answer"]


def process_langchain_rag_project2(proj_id, query):
    (
        Chroma,
        _,
        SentenceTransformerEmbeddings,
        RecursiveCharacterTextSplitter,
        _,
        ChatPromptTemplate,
        _,
    ) = get_rag_dependencies()
    ConversationalRetrievalChain, LLMChain, load_qa_chain, ConversationBufferWindowMemory = get_legacy_chain_dependencies()

    try:
        proj = Project.objects.get(pk=proj_id)
    except Project.DoesNotExist:
        raise ValueError(f"Project not found: {proj_id}")

        # Create a Document directly from the project content
    docs = [Document(page_content=proj.content, metadata={"source": f"project_{proj_id}"})]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    documents = text_splitter.split_documents(docs)

    import uuid
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    collection_name = f"proj2_{proj_id}_{uuid.uuid4().hex}"
    vector_store = Chroma.from_documents(documents, embedding_function, collection_name=collection_name)
    retriever = vector_store.as_retriever()

    model = get_chat_model()

    memory = ConversationBufferWindowMemory(
        memory_key='chat_history',
        return_messages=True,
        k=3
    )

    prompt = ChatPromptTemplate.from_template("""
    You are an AI assistant tasked with answering questions based on provided context.
    If the context does not contain enough information to answer the question,
    use your general knowledge to assist.
    Here is the context you have:
    {context}
    Chat History: {chat_history}
    Human: {question}
    AI: """)

    #   document_chain = create_stuff_documents_chain(model, prompt)
    #   retrieval_chain = create_retrieval_chain(retriever, document_chain)
    #   response = retrieval_chain.invoke({"input": query})

    qa_chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    conversation = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        memory=memory,
        question_generator=LLMChain(llm=model, prompt=prompt),
        combine_docs_chain=qa_chain
    )
    response = conversation({"question": query})

    try:
        vector_store.delete_collection()
    except Exception:
        pass

    return response["answer"]
