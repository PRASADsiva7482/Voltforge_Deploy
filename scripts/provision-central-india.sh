#!/usr/bin/env bash
# =============================================================================
# VoltForge — 100% Free Tier Provisioning in Central India (Pune)
# =============================================================================
set -euo pipefail

RESOURCE_GROUP="rg-voltforge-centralindia"
LOCATION="centralindia"
VM_NAME="voltforge-vm-india"
VM_SIZE="Standard_B1s"
ADMIN_USERNAME="azureuser"
VNET_NAME="voltforge-india-vnet"
SUBNET_NAME="voltforge-india-subnet"
NSG_NAME="voltforge-india-nsg"
IP_NAME="voltforge-india-ip"

echo "=========================================================="
echo "    VoltForge Central India (Free Tier Standard_B1s)      "
echo "=========================================================="
echo "Region:          ${LOCATION} (Pune, India)"
echo "Resource Group:  ${RESOURCE_GROUP}"
echo "VM Size:         ${VM_SIZE} (Free Tier 750 hrs/mo)"
echo "=========================================================="

echo "[1/5] Creating resource group ${RESOURCE_GROUP}..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output none

echo "[2/5] Creating Network Security Group & open ports (80, 443, 22)..."
az network nsg create --resource-group "${RESOURCE_GROUP}" --name "${NSG_NAME}" --location "${LOCATION}" --output none
az network nsg rule create --resource-group "${RESOURCE_GROUP}" --nsg-name "${NSG_NAME}" --name "Allow-HTTP" --priority 100 --direction Inbound --access Allow --protocol Tcp --destination-port-ranges 80 --output none
az network nsg rule create --resource-group "${RESOURCE_GROUP}" --nsg-name "${NSG_NAME}" --name "Allow-HTTPS" --priority 110 --direction Inbound --access Allow --protocol Tcp --destination-port-ranges 443 --output none
az network nsg rule create --resource-group "${RESOURCE_GROUP}" --nsg-name "${NSG_NAME}" --name "Allow-SSH" --priority 120 --direction Inbound --access Allow --protocol Tcp --destination-port-ranges 22 --output none

echo "[3/5] Allocating Public IP..."
az network public-ip create --resource-group "${RESOURCE_GROUP}" --name "${IP_NAME}" --location "${LOCATION}" --sku Standard --allocation-method Static --output none

echo "[4/5] Creating Virtual Network and Subnet..."
az network vnet create --resource-group "${RESOURCE_GROUP}" --name "${VNET_NAME}" --location "${LOCATION}" --address-prefix 10.1.0.0/16 --subnet-name "${SUBNET_NAME}" --subnet-prefix 10.1.1.0/24 --network-security-group "${NSG_NAME}" --output none

echo "[5/5] Provisioning Ubuntu 22.04 LTS VM (${VM_SIZE})..."
az vm create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${VM_NAME}" \
    --location "${LOCATION}" \
    --image "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest" \
    --size "${VM_SIZE}" \
    --admin-username "${ADMIN_USERNAME}" \
    --admin-password "VoltForge@2026!" \
    --authentication-type password \
    --vnet-name "${VNET_NAME}" \
    --subnet "${SUBNET_NAME}" \
    --public-ip-address "${IP_NAME}" \
    --nsg "${NSG_NAME}" \
    --output none

echo "[*] Enabling Auto-shutdown at 20:00 (8:00 PM IST)..."
az vm auto-shutdown --resource-group "${RESOURCE_GROUP}" --name "${VM_NAME}" --time 2000 --timezone "India Standard Time" --output none || true

NEW_IP=$(az network public-ip show --resource-group "${RESOURCE_GROUP}" --name "${IP_NAME}" --query ipAddress --output tsv)

echo ""
echo "=========================================================="
echo "      SUCCESS! VoltForge VM Created in Central India      "
echo "=========================================================="
echo "Public IP: ${NEW_IP}"
echo "Location:  Central India"
echo "Size:      Standard_B1s (1 vCPU, 1 GB RAM — Free Tier)"
echo "Auto-off:  20:00 IST (Daily)"
echo "=========================================================="
echo "Copy this Public IP: ${NEW_IP} and paste it into Antigravity chat!"
echo "=========================================================="
