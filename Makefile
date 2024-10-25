docker-build:
	docker build -t ncc-web-bot .

docker-run:
	docker stop ncc-web-bot || true
	docker rm ncc-web-bot || true
	docker run -p 3030:3030 \
		--name ncc-web-bot \
		-v /home/is/yuka-ot/ncc-web-bot/data:/bot/data \
		-e STREAMLIT_SERVER_PORT=3030 \
		-e STREAMLIT_SERVER_ADDRESS="0.0.0.0" \
		-e STREAMLIT_BROWSER_SERVER_ADDRESS="aoi.naist.jp" \
		-e STREAMLIT_BROWSER_BASE_URL="/brecobot-counselor-chat" \
		-e STREAMLIT_BROWSER_SERVER_PORT=3030 \
		ncc-web-bot /bin/bash -c "source ~/.bashrc && rye run streamlit run login.py"

docker-stop:
	docker stop ncc-web-bot

docker-rm:
	docker rm ncc-web-bot

docker-logs:
	docker logs -f ncc-web-bot
