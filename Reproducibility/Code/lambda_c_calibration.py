import pickle
import math
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

PKL_FILE = "output/network.pkl"

# lambdas to test
TEST_LAMBDAS = [0.01, 0.02, 0.05, 0.1]


# -------------------------------
# load graph
# -------------------------------

with open(PKL_FILE, "rb") as f:
    G = pickle.load(f)

print("Graph loaded")
print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())


# -------------------------------
# extract edge data
# -------------------------------

weights = []
p_uv_existing = []

for u, v, data in G.edges(data=True):
    w = data.get("weight", 1)
    weights.append(w)

    if "p_uv" in data:
        p_uv_existing.append(data["p_uv"])

weights = np.array(weights)

print("\nWeight statistics")
print("min:", weights.min())
print("max:", weights.max())
print("mean:", weights.mean())
print("median:", np.median(weights))


# -------------------------------
# inspect existing p_uv
# -------------------------------

if p_uv_existing:
    p_uv_existing = np.array(p_uv_existing)

    print("\nExisting p_uv statistics")
    print("min:", p_uv_existing.min())
    print("max:", p_uv_existing.max())
    print("mean:", p_uv_existing.mean())
    print("median:", np.median(p_uv_existing))

    print("\nPercentiles")
    for p in [50, 75, 90, 95, 99]:
        print(f"{p}th:", np.percentile(p_uv_existing, p))


# -------------------------------
# simulate p_uv for different lambdas
# -------------------------------

print("\nSimulated p_uv distributions")

for lam in TEST_LAMBDAS:

    p_values = 1 - np.exp(-lam * weights)

    print(f"\nlambda = {lam}")
    print("  mean:", p_values.mean())
    print("  median:", np.median(p_values))
    print("  90th:", np.percentile(p_values, 90))
    print("  99th:", np.percentile(p_values, 99))
    print("  max:", p_values.max())


# -------------------------------
# visualize distributions
# -------------------------------

plt.figure()

plt.hist(weights, bins=40)
plt.title("Collaboration Weight Distribution")
plt.xlabel("collaboration count")
plt.ylabel("edges")

plt.figure()

for lam in TEST_LAMBDAS:
    p_values = 1 - np.exp(-lam * weights)
    plt.hist(p_values, bins=40, alpha=0.5, label=f"λ={lam}")

plt.title("p_uv Distribution for Different λ")
plt.xlabel("p_uv")
plt.ylabel("edges")
plt.legend()

plt.show()


print("\nEdge weight distribution")

for p in [50, 75, 90, 95, 99]:
    print(f"{p}th percentile weight:", np.percentile(weights, p))