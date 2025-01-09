# Get docker if it isn't already installed
if ! command -v docker &> /dev/null; then
  echo "Docker is not installed. Installing Docker..."
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc

  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  # Post install steps
  sudo groupadd docker || true
  sudo usermod -aG docker $USER
  newgrp docker
else
  echo "Docker is already installed."
fi

# Curl and get airbyte
curl -LsfS https://get.airbyte.com | bash -

# Write values.yaml file
VALUES_YAML_CONTENT="global:
  auth:
    cookieSameSiteSetting: \"None\""

echo "$VALUES_YAML_CONTENT" > values.yaml
echo "values.yaml file created successfully."

# Write default admin password
SECRET_YAML_CONTENT="apiVersion: v1
  kind: Secret
  metadata:
    name: airbyte-auth-secrets
  type: Opaque
  stringData:
    instance-admin-password: easier"

echo "$VALUES_YAML_CONTENT" > secret.yaml
echo "secret.yaml file created successfully."

# Install airbyte with abctl
abctl local install --values ./values.yaml --secret ./secret.yaml
