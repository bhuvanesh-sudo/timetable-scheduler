# 1. Use Node.js (matches your local environment)
FROM node:22-alpine

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy package files first (better caching)
COPY package.json package-lock.json ./

# 4. Install dependencies
RUN npm install

# 5. Copy the rest of your code
COPY . .

# 6. Open the port Vite uses
EXPOSE 5173

# 7. Start Vite (HOST is needed for Docker mapping)
CMD ["npm", "run", "dev", "--", "--host"]