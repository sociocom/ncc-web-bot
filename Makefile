run:
	rye run uvicorn main:app --reload  --port=8000

open-port:
	ngrok http 8000 --region jp
