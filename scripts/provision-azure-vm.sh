#!/usr/bin/env bash
# =============================================================================
# VoltForge — Azure VM Provisioning Script
# Execute directly in Azure Cloud Shell (Bash) or any machine with Azure CLI
# =============================================================================
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
RESOURCE_GROUP="Voltforge"
LOCATION="centralindia"
VM_NAME="voltforge-vm"
VM_SIZE="Standard_B2ms"
ADMIN_USERNAME="azureuser"
VNET_NAME="voltforge-vnet"
SUBNET_NAME="voltforge-subnet"
NSG_NAME="voltforge-nsg"
IP_NAME="voltforge-public-ip"

# Generate a unique DNS label (lowercase alphanumeric)
RANDOM_SUFFIX=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 5 | head -n 1)
DNS_PREFIX="voltforge-${RANDOM_SUFFIX}"

echo "=========================================================="
echo "      VoltForge Azure Infrastructure Provisioning         "
echo "=========================================================="
echo "Resource Group:  ${RESOURCE_GROUP}"
echo "Location:        ${LOCATION}"
echo "VM Name:         ${VM_NAME}"
echo "VM Size:         ${VM_SIZE}"
echo "DNS Prefix:      ${DNS_PREFIX}"
echo "=========================================================="

# 1. Verify Resource Group
echo "[1/6] Verifying resource group ${RESOURCE_GROUP}..."
if ! az group show --name "${RESOURCE_GROUP}" >/dev/null 2>&1; then
    echo "[*] Creating resource group ${RESOURCE_GROUP} in ${LOCATION}..."
    az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output none
else
    echo "[+] Resource group ${RESOURCE_GROUP} exists."
fi

# 2. Create Network Security Group & Rules
echo "[2/6] Configuring Network Security Group and firewall rules..."
az network nsg create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${NSG_NAME}" \
    --location "${LOCATION}" \
    --output none

# Allow HTTP (Port 80)
az network nsg rule create \
    --resource-group "${RESOURCE_GROUP}" \
    --nsg-name "${NSG_NAME}" \
    --name "Allow-HTTP" \
    --priority 100 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --destination-port-ranges 80 \
    --output none

# Allow HTTPS (Port 443)
az network nsg rule create \
    --resource-group "${RESOURCE_GROUP}" \
    --nsg-name "${NSG_NAME}" \
    --name "Allow-HTTPS" \
    --priority 110 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --destination-port-ranges 443 \
    --output none

# Allow SSH (Port 22)
az network nsg rule create \
    --resource-group "${RESOURCE_GROUP}" \
    --nsg-name "${NSG_NAME}" \
    --name "Allow-SSH" \
    --priority 120 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --destination-port-ranges 22 \
    --output none

# Allow Direct Testing Ports (8080 Keycloak, 2001 BL, 2002 AI)
az network nsg rule create \
    --resource-group "${RESOURCE_GROUP}" \
    --nsg-name "${NSG_NAME}" \
    --name "Allow-Direct-Ports" \
    --priority 130 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --destination-port-ranges 8080 2001 2002 \
    --output none

# 3. Create Public IP with FQDN DNS label
echo "[3/6] Allocating Public IP with DNS name ${DNS_PREFIX}.${LOCATION}.cloudapp.azure.com..."
az network public-ip create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${IP_NAME}" \
    --location "${LOCATION}" \
    --allocation-method Static \
    --sku Standard \
    --dns-name "${DNS_PREFIX}" \
    --output none

# 4. Create Virtual Network and Subnet
echo "[4/6] Creating Virtual Network and Subnet..."
az network vnet create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${VNET_NAME}" \
    --location "${LOCATION}" \
    --address-prefix 10.0.0.0/16 \
    --subnet-name "${SUBNET_NAME}" \
    --subnet-prefix 10.0.1.0/24 \
    --network-security-group "${NSG_NAME}" \
    --output none

# 5. Create Cloud-Init configuration to install Docker on first boot
echo "[5/6] Preparing Cloud-Init automation script..."
CLOUD_INIT_FILE=$(mktemp /tmp/cloud-init-voltforge.XXXXXX.yml)
cat <<'EOF' > "${CLOUD_INIT_FILE}"
#cloud-config
package_upgrade: true
packages:
  - apt-transport-https
  - ca-certificates
  - curl
  - gnupg
  - lsb-release
  - git
  - ufw
  - unzip

runcmd:
  # Add Docker official repository
  - install -m 0755 -d /etc/apt/keyrings
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  - chmod a+r /etc/apt/keyrings/docker.asc
  - echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  - apt-get update -y
  - apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker azureuser
  - mkdir -p /opt/voltforge
  - chown -R azureuser:azureuser /opt/voltforge
EOF

# 6. Create the Azure Virtual Machine
echo "[6/6] Provisioning Ubuntu 22.04 LTS VM (${VM_SIZE}) in ${RESOURCE_GROUP}..."
az vm create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${VM_NAME}" \
    --location "${LOCATION}" \
    --image "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest" \
    --size "${VM_SIZE}" \
    --admin-username "${ADMIN_USERNAME}" \
    --generate-ssh-keys \
    --vnet-name "${VNET_NAME}" \
    --subnet "${SUBNET_NAME}" \
    --public-ip-address "${IP_NAME}" \
    --nsg "${NSG_NAME}" \
    --custom-data "${CLOUD_INIT_FILE}" \
    --output json

rm -f "${CLOUD_INIT_FILE}"

# Retrieve Public IP and FQDN
PUBLIC_IP=$(az network public-ip show --resource-group "${RESOURCE_GROUP}" --name "${IP_NAME}" --query ipAddress --output tsv)
FQDN=$(az network public-ip show --resource-group "${RESOURCE_GROUP}" --name "${IP_NAME}" --query dnsSettings.fqdn --output tsv)

echo ""
echo "=========================================================="
echo "          VoltForge VM Provisioning Complete!             "
echo "=========================================================="
echo "Public IP Address: ${PUBLIC_IP}"
echo "Public Domain:     http://${FQDN}"
echo "SSH Command:       ssh ${ADMIN_USERNAME}@${PUBLIC_IP}"
echo ""
echo "Next steps:"
echo "1. Upload your code to the VM: scp -r <voltforge-folder> ${ADMIN_USERNAME}@${PUBLIC_IP}:/opt/voltforge"
echo "2. SSH into VM: ssh ${ADMIN_USERNAME}@${PUBLIC_IP}"
echo "3. Run: cd /opt/voltforge/azureDeploy && ./scripts/deploy-all.sh"
echo "=========================================================="
