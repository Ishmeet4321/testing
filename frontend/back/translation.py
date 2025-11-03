import pandas as pd
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

def translate_hindi_to_english(hindi_text, model_name="facebook/nllb-200-distilled-600M"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    inputs = tokenizer(hindi_text, return_tensors="pt")
    translated_tokens = model.generate(**inputs)
    translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
    return translated_text
