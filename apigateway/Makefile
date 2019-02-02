
install: install-node install-serverless


install-node:
	@echo
	@echo "==> Installing NodeJS and npm"
	@test -e "`which node`" || brew install node


install-serverless:
	@echo
	@echo "==> Installing Serverless npm dependency"
	@test -e "`which serverless`" || sudo npm install -g serverless
