from transformers import pipeline

p = pipeline('sentiment-analysis', model='distilbert/distilbert-base-uncased-finetuned-sst-2-english')
print('Model downloaded successfully')
