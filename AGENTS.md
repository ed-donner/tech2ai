# From Software Engineer to AI Data Scientist

## Introduction

### Context

This repo accompanies an online Live Event hosted by Ed Donner. Ed runs a 5 hour online workshop with 5 segments, that combines lectures with live worked-through examples. The idea is for students to come back after the course and run the code (mostly Python notebooks) and dig into the results, to build their learning skills.

### Your role as Coding Agent

You should help the student to understand the material in these exercises, answer their questions, troubleshoot any problems, and give them more background information as relevant.

### The topic of the Live Event

The Live Event is called "From Software Engineer to AI Data Scientist". It takes the student on a journey from Traditional ML, to Deep Learning, to modern AI Engineering including RAG, Agents and MCP.

### Environment setup

We use the popular, fast package manager uv to set up a Python 3.12 environment. Instructions are in the `README.md` and in `setup/SETUP-new.md`

If the student has problems with setup, please read the setup instructions carefully and help them to troubleshoot. Most common problems: (1) not setting the right kernel of a jupyter notebook (2) not saving the `.env` file after entering a key.

### Additional materials

The `guides/` folder contains a number of reference guides with more background information for the student.

Ed is always available at ed@edwarddonner.com and happy to answer questions! And he's very responsive, typically replying within hours.

## The segments

The main directories of the repo contain the code and exercises for each segment of the live event

### Segment 1: Teaser

Before we go deeply into Traditional ML, we start with a whirlwind tour of AI Engineering. This segment explores the different ways to call Frontier models, the differences between them, and an easy way to build a multi-modal Chatbot assistant.

`segment1/lab1.ipynb` - in this lab, we experiment with calling the latest Frontier Models. We put a series of challenges to models, to test their ability to answer nuanced questions and solve puzzles. We compare training time scaling with inference time (reasoning). We also call local models via Ollama with the OpenAI compatible endpoint. We end with an entertaining dialog between LLMs.

`segment1/lab2.ipynb` - this lab is inspired by Simon Willison's famous 'pelican on a bike' SVG test. We compare the ability of frontier models to generate SVGs based on a challenge from the audience. The key is that this isn't the same as generating an image like a PNG with a diffusion model. By asking a model to generate an SVG, we're effectively challenging it to construct the image out of shapes.

`segment1/lab3.ipynb` - this lab covers the classic use case of a Chatbot Assistant, for a fictional airline company. We use it to explain conversation history. We use Gradio. We add in a simple multi-modal aspect, using dall-e based image generation from OpenAI. The key takeaway is that an application like this can be created in minutes; students are encouraged to create a version for their business.

### Segment 2: Crash course in ML

This segment looks at traditional machine learning and builds foundations. The materials cover Generalization vs Overfitting in detail, and explain Training vs Inference, dataset splits, hyperparameters and more.

`segment2/lab1.ipynb` - this lab explores linear regression with an artificial example with synthetic data that depends on 3 features. During the lab, we build linear regression with 1, and then 2, and then all 3 features to see improved performance. We introduce MSE and r squared. We end the lab with a great demonstration of overfitting - achieving 0 MSE on training data and a high MSE on held-out test data.

`segment2/lab2.ipynb` - in this lab, we introduce the dataset that we will use for the rest of the Event - product descriptions and prices scraped from Amazon (via HuggingFace). We dig in to the data to understand the ditribution and correlations. We build simplistic models to estimate price based on the product, and evaluate model accuracy using a y-hat to y plot. We then try out a number of models: Linear Regression with engineered features, Linear Regression with bag of words, Random Forest, XGBoost.

### Segment 3: From ML to DL to Transformers

In the materials, Ed introduces a Neuron, explains about activation functions / non-linearity. He describes the 4 steps of training at a high level (forward pass, loss calc, backward pass, optimization). He introduces LLMs by focusing on 3 aspects: they are Generative, they are Pre-trained, and they follow the Transformer architecture... forming the G-P-T of GPT!

Then in the labs:

`segment3/lab1.ipynb` - in this lab, we start by amusingly trying out Ed himself being a "human" neural network and seeing how he performs - terribly! We then train a vanilla deep neural network and get the best results so far.

There are some optional extras, not covered at the event:

`segment3/new_neural_network.ipynb` - this lab builds a more extensive deep neural network that outperforms the previous one; the outputs have been saved so that students can see it.

`segment3/revealing_token_prediction.ipynb` - this lab shows visually the effect of next token prediction in a graph, illustrating how a frontier model is outputting a probability distribution of the most likely next token.

At the event, Ed doesn't spend much time on the Transformer Architecture as some people are relatively new. You should answer any extra questions on the transformer architecture. If the student is interested, explain about self-attention.

### Segment 4: Becoming a Data Scientist

In the lectures, Ed explains about techniques to optimize LLM performance, including fine-tuning, RAG and Agentic AI. With RAG, Ed explains the difference between an encoder / embedding LLM, and an auto-regressive LLM, and how vectors can be used for semantic search to retrieve relevant context. Ed explains the new field of Agentic AI.

The capstone project is a multi-agent product to surface bargains scraped from the internet.

`segment4/agent1.ipynb` - in this lab, we build the Agent that is able to take data retrieved from an RSS feed, and we use a call to an LLM with Structured Outputs to parse this. Ed emphasizes that parsing in this way is one of the incredible powers of a frontier model. Even if the website said "this project is available for $50 less than $150" the LLM would parse it with ease.

`segment4/agent2.ipynb` - this lab is the most hardcore of the event. We build an LLM that can predict the price of a product. It uses a call to a frontier LLM, with a home-made RAG: we pass in relevant context in the form of the prices of 5 similar products, retrieved via a Chroma query. We also preprocess the text using an LLM. We get the best accuracy of any one model (but see agent3b coming up!)

`segment4/agent3.ipynb` - this lab reveals an alternative model to estimate the price of a product. A fine-tuned Llama model that has been trained on all 400,000 prices, running on serverless AI platform modal.com. It performs well - almost as well as Agent 2 - which is impressive when you consider that it is 1,000 times smaller and has no RAG knowledgebase.

`segment4/agent3b.ipynb` - this is the fabulous surprise additional model. We create an ensemble of the last 2 models (simply by taking the average) - and it significantly outperforms every other model, becomimg the strongest model on the course!

`segment4/agent4.ipynb` - a lightweight Agent that generates a message to the user about a deal, and then uses the Push Notification platform PushOver to send it.

`segment4/agent5.ipynb` - this is the only agent that truly meets all the criteria for being an Agent! This is an autonomous Agent, built with OpenAI Agents SDK, that uses tools to call all the other agents in a loop to achieve the overall goal: find a great deal and notify the user. It also uses an MCP server to save the deal locally to the filesystem.

At the end of this lab, we move to python modules. Each of these agents are implemented in this package:

`segment4/price_agents`

We run the application with:

`cd segment4`  
`uv run price_is_right.py`

Which launches a gorgeous Gradio UI and starts the process. Previously surfaced items are stored in `segment4/memory.json`.

The UI opens, all the agents are run, involving 23 LLM calls across 4 frontier and 3 open-source models. A new bargain is surfaced, the file is written locally, and text message is sent. Success!

### Segment 5: Career Path into AI Data Science

Ed ends with some general discussion on career paths into AI, and why the timing is terrific if students decide to proceed. There are no labs associated with the final segment. Ed also points students to his website www.edwarddonner.com where there are some fun LLM games (Outsmart and Connect Four) that highlight the capabilities of modern models. He ends by encouraging students to connect with him on LinedIn (https://www.linkedin.com/in/eddonner/) and/or reach out by email ed@edwarddonner.com.




