import numpy as np
import random
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

SEED = 42

def create_random_model(n_classes):
    t = random.choice(["rf","xgb","et","lgbm"])
    if t == "rf":
        return RandomForestClassifier(
            n_estimators=random.randint(100,400),
            max_depth=random.choice([8,12,16,None]),
            min_samples_split=random.choice([2,4,8]),
            class_weight="balanced", random_state=random.randint(0,999))
    elif t == "xgb":
        return XGBClassifier(
            n_estimators=random.randint(100,400),
            max_depth=random.randint(3,8),
            learning_rate=random.uniform(0.03,0.15),
            subsample=random.choice([0.8,1.0]),
            colsample_bytree=random.choice([0.8,1.0]),
            objective="multi:softprob", num_class=n_classes,
            eval_metric="mlogloss", use_label_encoder=False,
            random_state=random.randint(0,999), verbosity=0)
    elif t == "et":
        return ExtraTreesClassifier(
            n_estimators=random.randint(100,400),
            max_depth=random.choice([8,12,16,None]),
            class_weight="balanced", random_state=random.randint(0,999))
    else:
        return LGBMClassifier(
            n_estimators=random.randint(100,400),
            max_depth=random.randint(3,10),
            learning_rate=random.uniform(0.03,0.15),
            class_weight="balanced", random_state=random.randint(0,999), verbosity=-1)

class Individual:
    def __init__(self, n_classes):
        self.n_classes = n_classes
        pool_size = random.randint(2,4)
        self.models = [create_random_model(n_classes) for _ in range(pool_size)]
        w = np.random.rand(pool_size)
        self.weights = w / w.sum()
        self.fitness = 0.0
        self.f1 = 0.0

    def train(self, X_train, y_train):
        for m in self.models:
            m.fit(X_train, y_train)

    def predict_proba(self, X):
        probs = np.zeros((X.shape[0], self.n_classes))
        for w, m in zip(self.weights, self.models):
            probs += w * m.predict_proba(X)
        return probs

    def predict(self, X):
        return np.argmax(self.predict_proba(X), axis=1)

    def evaluate(self, X_val, y_val):
        preds = self.predict(X_val)
        self.fitness = accuracy_score(y_val, preds)
        self.f1 = f1_score(y_val, preds, average="macro", zero_division=0)

def crossover(p1, p2):
    child = Individual.__new__(Individual)
    child.n_classes = p1.n_classes
    split = max(1, len(p1.models) // 2)
    child.models = p1.models[:split] + p2.models[split:]
    w = np.random.rand(len(child.models))
    child.weights = w / w.sum()
    child.fitness = 0.0
    child.f1 = 0.0
    return child

def mutate(individual, rate=0.3):
    for i in range(len(individual.models)):
        if random.random() < rate:
            individual.models[i] = create_random_model(individual.n_classes)
    noise = np.random.rand(len(individual.weights)) * 0.2
    w = individual.weights + noise
    individual.weights = w / w.sum()
    return individual

class SLEEM:
    def __init__(self, population_size=10, generations=8, elite_size=3):
        self.population_size = population_size
        self.generations = generations
        self.elite_size = elite_size
        self.best = None
        self.history = []

    def fit(self, X, y):
        n_classes = len(np.unique(y))
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=SEED, stratify=y)
        population = [Individual(n_classes) for _ in range(self.population_size)]

        for gen in range(self.generations):
            print(f"\n{'='*52}\n  Generation {gen+1}/{self.generations}\n{'='*52}")
            for i, ind in enumerate(population):
                ind.train(X_train, y_train)
                ind.evaluate(X_val, y_val)
                names = [type(m).__name__ for m in ind.models]
                print(f"  [{i+1:02d}] Acc={ind.fitness:.4f} F1={ind.f1:.4f} {names}")

            population.sort(key=lambda x: x.fitness, reverse=True)
            best = population[0]
            self.history.append({"generation":gen+1,
                                  "best_accuracy":round(best.fitness,4),
                                  "best_f1":round(best.f1,4)})
            print(f"\n  Best: Acc={best.fitness:.4f} F1={best.f1:.4f}")
            if gen == self.generations - 1:
                break

            elites = population[:self.elite_size]
            new_pop = elites.copy()
            while len(new_pop) < self.population_size:
                p1, p2 = random.sample(elites, 2)
                child = mutate(crossover(p1, p2))
                new_pop.append(child)
            population = new_pop

        self.best = population[0]
        print(f"\n  Final Best: Acc={self.best.fitness:.4f} F1={self.best.f1:.4f}")

    def predict(self, X):
        return self.best.predict(X)

    def predict_proba(self, X):
        return self.best.predict_proba(X)