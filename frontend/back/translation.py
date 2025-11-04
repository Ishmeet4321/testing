'''import pandas as pd
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

m2m_model_name = "facebook/m2m100_418M"
m2m_tokenizer = M2M100Tokenizer.from_pretrained(m2m_model_name)
m2m_model = M2M100ForConditionalGeneration.from_pretrained(m2m_model_name)

def translate_hi_to_en(hindi_text):
    if not hindi_text.strip():
        return ""
    m2m_tokenizer.src_lang = "hi"
    encoded = m2m_tokenizer(hindi_text, return_tensors="pt")
    generated_tokens = m2m_model.generate(**encoded, forced_bos_token_id=m2m_tokenizer.get_lang_id("en"))
    return m2m_tokenizer.decode(generated_tokens[0], skip_special_tokens=True)



def translate_hindi_to_english(hindi_text, model_name="facebook/m2m100_418M"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    inputs = tokenizer(hindi_text, return_tensors="pt")
    translated_tokens = model.generate(**inputs)
    translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
    return translated_text
'''