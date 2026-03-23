FROM python:3.11-slim-bookworm

# System dependencies: dev tools + Node.js + firewall utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl sudo ca-certificates ripgrep fd-find jq \
    iptables ipset iproute2 dnsutils \
    gnupg \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Create dev user with sudo access
RUN useradd -m -s /bin/bash dev \
  && echo "dev ALL=(ALL) NOPASSWD: ALL" \
    >> /etc/sudoers.d/dev-nopasswd \
  && chmod 0440 /etc/sudoers.d/dev-nopasswd

# Copy firewall script into the image
COPY init-firewall.sh /usr/local/bin/init-firewall.sh
RUN chmod +x /usr/local/bin/init-firewall.sh

# Ensure the claude config dir exists with correct ownership
RUN mkdir -p /home/dev/.claude && chown dev:dev /home/dev/.claude

USER dev
WORKDIR /workspace
