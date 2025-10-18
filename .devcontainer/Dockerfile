FROM python:3.14

# Create user 'mike' with home directory and add to sudoers
RUN useradd -ms /bin/bash mike \
    && apt-get update \
    && apt-get install -y sudo \
    && echo "mike ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER mike
WORKDIR /home/mike
