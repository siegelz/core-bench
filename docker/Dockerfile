# Use an official Python runtime as a parent image
FROM cruizba/ubuntu-dind:focal-latest

# Set the working directory
WORKDIR /capsule

# Copy the current directory contents into the container at /capsule
COPY . /capsule

# Install some packages
RUN apt-get update && apt-get install -y sudo && apt-get install -y wget
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata