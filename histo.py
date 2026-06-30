import numpy as np
import matplotlib.pyplot as plt # type: ignore

# =====================================================
# NUMBER OF COMPONENTS
# =====================================================

N = 20

# =====================================================
# ORDERED COMPONENTS
# =====================================================

components = [f"$x_{{{i}}}$" for i in range(1, N+1)]

# =====================================================
# RANDOM INTEGER WEIGHTS
# =====================================================

weights = np.random.randint(
    low=0,      # minimum weight
    high=11,    # one above the maximum weight
    size=N
)

positions = np.arange(1, N+1)
centre_of_mass = np.sum(positions * weights) / np.sum(weights)
print("Centre of Mass =", centre_of_mass)


plt.axvline(
    centre_of_mass,
    color="red",
    linewidth=3,
    linestyle="--",
    label="Centre of Mass"
)

plt.legend()


# =====================================================
# PLOT
# =====================================================

plt.figure(figsize=(16,6))

bars = plt.bar(
    components,
    weights,
    color="steelblue",
    edgecolor="black",
    linewidth=1.5
)

plt.title(
    "Weighted Ordered Components",
    fontsize=18,
    fontweight="bold"
)

plt.xlabel("Ordered Components", fontsize=14)
plt.ylabel("Weight", fontsize=14)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4
)

# Show weight above every bar
for bar, weight in zip(bars, weights):

    plt.text(
        bar.get_x() + bar.get_width()/2,
        weight + 0.15,
        str(weight),
        ha="center",
        fontsize=10
    )

plt.tight_layout()
plt.show()


