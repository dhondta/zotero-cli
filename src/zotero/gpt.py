# -*- coding: UTF-8 -*-
import _pickle
import pdfminer
import pptx
import requests
from chromadb.config import Settings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.document_loaders import *
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import GPT4All, LlamaCpp
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from multiprocessing import Pool
from tinyscript import logging, os, sys
from tinyscript.helpers import colored, get_terminal_size, std_input, Path, TempPath
from tqdm import tqdm


__all__ = ["ask", "ingest", "install", "select", "MODEL_DEFAULT_NAME", "MODEL_NAMES", "MODELS"]

# Code hereafter is inspired from: https://github.com/imartinez/privateGPT

CHUNK_OVERLAP = 50
CHUNK_SIZE = 500
DB_PATH = Path("~/.zotero/db", create=True, expand=True)
EMBEDDINGS = "all-MiniLM-L6-v2"
LOADERS = {
    ".csv":  CSVLoader,
    ".docx": Docx2txtLoader,
    ".doc":  UnstructuredWordDocumentLoader,
    ".docx": UnstructuredWordDocumentLoader,
    ".enex": EverNoteLoader,
    ".eml":  UnstructuredEmailLoader,
    ".epub": UnstructuredEPubLoader,
    ".html": UnstructuredHTMLLoader,
    ".md":   UnstructuredMarkdownLoader,
    ".odt":  UnstructuredODTLoader,
    ".pdf":  PDFMinerLoader,
    ".ppt":  UnstructuredPowerPointLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".txt":  (TextLoader, {"encoding": "utf8"}),
    # Add more mappings for other file extensions and loaders as needed
}
MODEL_DEFAULT_NAME = "ggml-gpt4all-j-v1.3-groovy.bin"
MODEL_LINK = "https://gpt4all.io/models/"
MODEL_N_CTX = 1000
MODEL_NAMES = [
    "ggml-gpt4all-j-v1.3-groovy.bin",
    "ggml-gpt4all-l13b-snoozy.bin",
    "ggml-mpt-7b-chat.bin",
    "ggml-v3-13b-hermes-q5_1.bin",
    "ggml-vicuna-7b-1.1-q4_2.bin",
    "ggml-vicuna-13b-1.1-q4_2.bin",
    "ggml-wizardLM-7B.q4_2.bin",
    "ggml-stable-vicuna-13B.q4_2.bin",
    "ggml-mpt-7b-base.bin",
    "ggml-nous-gpt4-vicuna-13b.bin",
    "ggml-mpt-7b-instruct.bin",
    "ggml-wizard-13b-uncensored.bin",
    "ggml-model-q4_0.bin",  #https://huggingface.co/Pi3141/alpaca-native-7B-ggml/resolve/397e872bf4c83f4c642317a5bf65ce84a105786e/
]
MODEL_PATH = Path("~/.zotero/models", create=True, expand=True)
SRC_PATH = Path("~/Zotero/", expand=True)
TARGET_SOURCE_CHUNKS = 4

CHROMA_SETTINGS = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory=str(DB_PATH),
    anonymized_telemetry=False,
)
if MODEL_PATH.joinpath("default").exists():
    MODEL_DEFAULT_NAME = MODEL_PATH.joinpath("default").read_text()
MODELS = [m.basename for m in MODEL_PATH.listdir() if m.basename != "default" and m.basename in MODEL_NAMES]


def _load_doc(path):
    """ Load the file from the given path with the relevant loader. """
    global logger
    logger.debug(path)
    loader, kwargs = LOADERS[Path(path).extension], {}
    if isinstance(loader, tuple) and len(loader) == 2:
        loader, kwargs = loader
    try:
        return loader(path, **kwargs).load()
    except Exception as e:
        logger.error("%s (%s)" % (path, str(e)))


def _load_docs(zotero_files=SRC_PATH, ignore=None, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,**kw):
    """ Load text chunks from Zotero documents. """
    global logger
    logger = kw.get('logger', logging.nullLogger)
    p, r = Path(zotero_files, expand=True).joinpath("storage"), []
    files = [f for f in map(str, p.walk(filter_func=lambda p: p.extension in LOADERS.keys())) if f not in ignore]
    logger.info("Loading Zotero documents...")
    with Pool(processes=os.cpu_count()) as pool, tqdm(total=len(files), ncols=get_terminal_size()[0]) as pbar:
        for docs in pool.imap_unordered(_load_doc, files):
            if docs:
                r.extend(docs)
            pbar.update()
    logger.debug("Splitting text from the loaded documents...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)


def ask(embeddings=EMBEDDINGS, target_source_chunks=TARGET_SOURCE_CHUNKS, mute_stream=True, model=MODEL_DEFAULT_NAME,
        model_type="GPT4All", model_n_ctx=MODEL_N_CTX, verbose=False, show_source=False, show_content=False,
        logger=logging.nullLogger, **kw):
    """ Open a prompt for querying Zotero documents. """
    m = MODEL_PATH.joinpath(Path(model, expand=True).basename)
    if not m.exists():
        install(model)
        m = MODEL_PATH.joinpath(Path(model, expand=True).basename)
    embeddings = HuggingFaceEmbeddings(model_name=embeddings)
    db = Chroma(persist_directory=str(DB_PATH), embedding_function=embeddings, client_settings=CHROMA_SETTINGS)
    retriever = db.as_retriever(search_kwargs={'k': target_source_chunks})
    callbacks = [] if mute_stream else [StreamingStdOutCallbackHandler()]
    if model_type == "GPT4All":
        llm = GPT4All(model=str(m), n_ctx=model_n_ctx, backend="gptj", callbacks=callbacks, verbose=verbose)
    elif model_type == "LlamaCpp":
        llm = LlamaCpp(model_path=str(m), n_ctx=model_n_ctx, callbacks=callbacks, verbose=verbose)
    else:
        logger.error("Bad model type (should be GPT4All or LlamaCpp)")
        sys.exit(1)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever,
                                     return_source_documents=show_source)
    try:
        while True:
            query = std_input("\nEnter a query: ", style=["bold", "cyan"])
            if query in ["exit", "x"]:
                return
            r = qa(query)
            answer = r['result']
            docs = [] if not show_source else r['source_documents']
            if len(docs) > 0:
                print(colored("\nSource documents: ", style=["bold", "cyan"]))
                for doc in docs:
                    print("-", doc.metadata["source"])
                    if show_content:
                        print(colored(doc.page_content, style=["white"]))
    except EOFError:
        sys.exit(0)


def ingest(zotero_files=SRC_PATH, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, embeddings=EMBEDDINGS,
           logger=logging.nullLogger, **kw):
    """ Ingest Zotero documents in the vectorstore. """
    embeddings = HuggingFaceEmbeddings(model_name=embeddings)
    if DB_PATH.joinpath("index").is_dir() and \
       DB_PATH.joinpath("chroma-collections.parquet").is_file() and \
       DB_PATH.joinpath("chroma-embeddings.parquet").is_file() and \
       len(list(DB_PATH.joinpath("index").walk(filter_func=lambda p: p.extension in [".bin", ".pkl"]))):
        logger.debug("Appending to existing vectorstore...")
        db = Chroma(persist_directory=str(DB_PATH), embedding_function=embeddings, client_settings=CHROMA_SETTINGS)
        collection = db.get()
        texts = load(zotero_files, [m['source'] for m in collection['metadatas']], chunk_size, chunk_overlap)
        logger.info("Creating embeddings, this may take a while...")
        db.add_documents(texts)
    else:
        logger.info("Creating new vectorstore...")
        texts = _load_docs(zotero_files, [], chunk_size, chunk_overlap, logger=logger)
        logger.info("Creating embeddings, this may take a while...")
        db = Chroma.from_documents(texts, embeddings, persist_directory=str(DB_PATH), client_settings=CHROMA_SETTINGS)
    db.persist()
    db = None
    logger.success("Ingestion of Zotero documents complete.")


def install(model=MODEL_DEFAULT_NAME, download=False, logger=logging.nullLogger, **kw):
    """ Install and select the input model in ~/.zotero folder ; download it if required. """
    m, fn = Path(model, expand=True), Path(model).basename
    if fn not in MODEL_NAMES:
        logger.warning("Model '%s' is not supported" % fn)
        sys.exit(0)
    if not MODEL_PATH.joinpath(fn).exists():
        if not m.exists():
            if download:
                link, model = MODEL_LINK + fn, TempPath(fn)
                logger.info("Downloading model '%s'" % fn)
                resp = requests.get(link, stream=True)
                l = resp.headers.get("content-length")
                with model.open("wb") as f:
                    if l is None:
                        model.write(resp.content)
                    else:
                        with tqdm(total=round(int(l)/4096+.5), ncols=get_terminal_size()[0]) as pbar:
                            for data in resp.iter_content(chunk_size=4096):
                                model.write(data)
                                pbar.update()
            else:
                logger.error("Input model '%s' does not exist !" % model)
                sys.exit(1)
        logger.info("Installing model '%s'..." % m)
        m.rename(MODEL_PATH.joinpath(fn))
        select(fn)
    else:
        logger.warning("Model '%s' already exists in %s" % (fn, MODEL_PATH))


def select(model=MODEL_DEFAULT_NAME, **kw):
    """ Select the input model from ~/.zotero folder. """
    MODEL_PATH.joinpath("default").write_text(model)

