from sklearn.neural_network import *
from Reg_Oracle_Fict import *
from MSR_Reduction import *
from sklearn import svm
from sklearn import neighbors

# USAGE: python Audit.py all 50

# Helper Functions


def get_fp(preds, y):
    """Return the fp rate of preds wrt to true labels y."""
    return np.mean([p for i,p in enumerate(preds) if y[i] == 0])


def audit(predictions, X, X_prime, y):
    """Takes in predictions on dataset (X, X',y) and prints gamma-unfairness,
    fp disparity, group size, group coefficients, and sensitive column names.
    """
    FP = get_fp(predictions, y)
    aud_group, gamma_unfair, fp_in_group, err_group, pos_neg = get_group(predictions, X_sens=X_prime, X=X, y_g=y, FP=FP)
    group_size = gamma_unfair/fp_in_group
    group_coefs = aud_group.b0.coef_ - aud_group.b1.coef_
    # get indices of maximum k coefficients
    k = np.min([len(group_coefs), 3])
    top_indices = np.abs(group_coefs).argsort()[-k:][::-1]
    print('accuracy: {}'.format(1-np.mean(np.abs(np.subtract(predictions, y)))))
    print('group size: {}, gamma-unfairness: {}, FP-disparity: {}'.format(group_size, gamma_unfair, fp_in_group))
    print('subgroup_coefficients: {}'.format(group_coefs),)
    print('sensitive attributes: {}'.format([c for c in X_prime.columns],))
    print('sensitive attributes with the largest group coefficients: {}'.format(X_prime.columns[top_indices]))
    print('coefficients of top sensitive attributes: {}'.format(group_coefs[top_indices]))


if __name__ == "__main__":
    random.seed(1)
    ds = ['communities', 'lawschool', 'adult', 'student']
    dataset, max_iters = sys.argv[1:]
    dataset = str(dataset)
    max_iters = int(max_iters)

    if dataset == 'all':
        for dataset in ds:
            # Data Cleaning and Import
            f_name = 'clean_{}'.format(dataset)
            clean_the_dataset = getattr(clean_data, f_name)
            X, X_prime, y = clean_the_dataset()

            # print out the invoked parameters
            num_sens = X_prime.shape[1]
            print('Invoked Parameters: number of sensitive attributes = {}, dataset = {}'.format(num_sens, dataset))

            # logistic regression
            model = linear_model.LogisticRegression()
            model.fit(X, y)
            yhat = list(model.predict(X))
            print('logistic regression audit:')
            audit(predictions=yhat, X=X, X_prime=X_prime, y=y)

            # shallow neural network
            # model = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(3, 2), random_state=1)
            # model.fit(X,y)
            # yhat = list(model.predict(X))
            # print('multilayer perceptron (3, 2) audit:')
            # audit(predictions=yhat, X=X, X_prime=X_prime, y=y)

            # support vector machine
            model = svm.SVC()
            model.fit(X, y)
            yhat = list(model.predict(X))
            print('SVM audit:')
            audit(predictions=yhat, X=X, X_prime=X_prime, y=y)

            # nearest neighbor
            model = neighbors.KNeighborsClassifier(3)
            model.fit(X, y)
            yhat = list(model.predict(X))
            print('nearest neighbors audit:')
            audit(predictions=yhat, X=X, X_prime=X_prime, y=y)

            # MSR reduction with Reg Oracle
            X, X_prime_cts, y = clean_the_dataset()
            n = X.shape[0]
            # threshold sensitive features by average value
            sens_means = np.mean(X_prime)
            for col in X_prime.columns:
                X.loc[(X[col] > sens_means[col]), col] = 1
                X_prime.loc[(X_prime[col] > sens_means[col]), col] = 1
                X.loc[(X[col] <= sens_means[col]), col] = 0
                X_prime.loc[(X_prime[col] <= sens_means[col]), col] = 0
            yhat = MSR_preds(X, X_prime, X_prime_cts, y, max_iters, False)
            audit(yhat, X, X_prime, y)
    else:
        # Data Cleaning and Import
        f_name = 'clean_{}'.format(dataset)
        clean_the_dataset = getattr(clean_data, f_name)
        X, X_prime, y = clean_the_dataset()

        # print out the invoked parameters
        num_sens = X_prime.shape[1]
        print('Invoked Parameters: number of sensitive attributes = {}, dataset = {}'.format(num_sens, dataset))

        # logistic regression
        model = linear_model.LogisticRegression()
        model.fit(X, y)
        yhat = list(model.predict(X))
        print('logistic regression audit:')
        audit(predictions=yhat, X=X, X_prime=X_prime, y=y)

        # shallow neural network
        # model = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(3, 2), random_state=1)
        # model.fit(X,y)
        # yhat = list(model.predict(X))
        # print('multilayer perceptron (3, 2) audit:')
        # audit(predictions=yhat, X=X, X_prime=X_prime, y=y)

        # support vector machine
        model = svm.SVC()
        model.fit(X, y)
        yhat = list(model.predict(X))
        print('SVM audit:')
        audit(predictions=yhat, X=X, X_prime=X_prime, y=y)

        # nearest neighbor
        model = neighbors.KNeighborsClassifier(3)
        model.fit(X, y)
        yhat = list(model.predict(X))
        print('nearest neighbors audit:')
        audit(predictions=yhat, X=X, X_prime=X_prime, y=y)

        # MSR reduction with Reg Oracle
        X, X_prime_cts, y = clean_the_dataset()
        n = X.shape[0]
        # threshold sensitive features by average value
        sens_means = np.mean(X_prime)
        for col in X_prime.columns:
            X.loc[(X[col] > sens_means[col]), col] = 1
            X_prime.loc[(X_prime[col] > sens_means[col]), col] = 1
            X.loc[(X[col] <= sens_means[col]), col] = 0
            X_prime.loc[(X_prime[col] <= sens_means[col]), col] = 0
        yhat = MSR_preds(X, X_prime, X_prime_cts, y, max_iters, False)
        audit(yhat, X, X_prime, y)
