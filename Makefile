run:
	rye run uvicorn main:app --reload  --port=8000

connect:
	ngrok http 8000 --region jp

docker-run:
	docker run -it --rm -p 3000:3000 \
	--name ncc-line-chatbot-poc -it \
	-v $(PWD)/data:/bot/data \
	ncc-line-chatbot-poc \
	/bin/bash -c "source ~/.bashrc && rye run uvicorn main:app --reload --host=0.0.0.0 --port=3000"

build:
	docker build . -t ncc-line-chatbot-poc