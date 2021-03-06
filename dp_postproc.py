import numpy as np
import pandas as pd
import cvxopt as cvx

class dp_postproc:
    
    def eq_odds(Yhat, A, Y, qhat, epsilon, gamma, beta, fp):

        # This function performs the DP_postprocessing algorithm of the paper.

        # Inputs:
        # Yhat: base classifier estimates
        # A: "binary" sensitive attribute
        # Y: true labels
        # qhat: empirical distribution of Yhat, A, Y
        # epsilon: privacy parameter
        # gamma: fairness violation
        # beta: confidence parameter
        # fp = 0 means eo fairness, fp = 1 means false positive parity

        # Outputs: 
        # errtilde: error
        # unftilde: fairness violation

        m = len(Y)
        rates = dp_postproc.rates(qhat)
        fpr0 = rates[0]
        fpr1 = rates[1]
        tpr0 = rates[2]
        tpr1 = rates[3]
        
        q_dp = qhat + np.random.laplace(scale= 2/(m*epsilon), size=8).reshape((2,2,2))
        minq_dp0 = np.min([q_dp[1,0,0] + q_dp[0,0,0], q_dp[1,1,0] + q_dp[0,1,0]]) 
        minq_dp1 = np.min([q_dp[1,0,1] + q_dp[0,0,1], q_dp[1,1,1] + q_dp[0,1,1]])
        fpr_bound = (4*np.log(8/beta))/(minq_dp0*m*epsilon)
        tpr_bound = (4*np.log(8/beta))/(minq_dp1*m*epsilon)
        if (fp == 0):
            if ( (fpr_bound < 0) or (tpr_bound < 0) ):
                return(-1,-1)
        if (fp == 1):
            if ( fpr_bound < 0 ):
                return(-1,-1)
        
        rates_dp = dp_postproc.rates(q_dp)
        fpr0_dp = rates_dp[0]
        fpr1_dp = rates_dp[1]
        tpr0_dp = rates_dp[2]
        tpr1_dp = rates_dp[3]
        
        if (fp == 0):
            B = cvx.matrix([ [fpr0_dp-1, 1-fpr0_dp, tpr0_dp-1, 1-tpr0_dp, 1, -1, 0, 0, 0, 0, 0, 0], #p00
                         [1-fpr1_dp, fpr1_dp-1, 1-tpr1_dp, tpr1_dp-1, 0, 0, 1, -1, 0, 0, 0, 0], #p01
                         [-fpr0_dp, fpr0_dp, -tpr0_dp, tpr0_dp, 0, 0, 0, 0, 1, -1, 0, 0], #p10
                         [fpr1_dp, -fpr1_dp, tpr1_dp, -tpr1_dp, 0, 0, 0, 0, 0, 0, 1, -1]], (12,4), 'd') #p11
            b = cvx.matrix([ gamma + fpr_bound, gamma + fpr_bound, gamma + tpr_bound, gamma + tpr_bound, 
                        1, 0, 1, 0, 1, 0, 1, 0 ], (12,1), 'd')
            c = cvx.matrix([ q_dp[0,0,0] - q_dp[0,0,1], q_dp[0,1,0] - q_dp[0,1,1], # p00, p01
                        q_dp[1,0,0] - q_dp[1,0,1], q_dp[1,1,0] - q_dp[1,1,1]], (4,1), 'd') # p10, p11
        if (fp == 1):
            B = cvx.matrix([ [fpr0_dp-1, 1-fpr0_dp, 1, -1, 0, 0, 0, 0, 0, 0], #p00
                         [1-fpr1_dp, fpr1_dp-1, 0, 0, 1, -1, 0, 0, 0, 0], #p01
                         [-fpr0_dp, fpr0_dp, 0, 0, 0, 0, 1, -1, 0, 0], #p10
                         [fpr1_dp, -fpr1_dp, 0, 0, 0, 0, 0, 0, 1, -1]], (10,4), 'd') #p11
            b = cvx.matrix([ gamma + fpr_bound, gamma + fpr_bound,
                            1, 0, 1, 0, 1, 0, 1, 0 ], (10,1), 'd')
            c = cvx.matrix([ q_dp[0,0,0] - q_dp[0,0,1], q_dp[0,1,0] - q_dp[0,1,1], # p00, p01
                        q_dp[1,0,0] - q_dp[1,0,1], q_dp[1,1,0] - q_dp[1,1,1]], (4,1), 'd') # p10, p11
        
        cvx.solvers.options['show_progress'] = False
        sol = cvx.solvers.lp(c,B,b)
        p = np.array(sol['x']).reshape((2,2))
        p[p > 1] = 1
        p[p < 0] = 0
        #Ytilde = dp_postproc.postproc_label(Yhat, A, p)
        #errtilde = dp_postproc.error(Ytilde, Y)
        #unftilde = dp_postproc.unfairness(Ytilde, A, Y)
        errtilde = ( (qhat[0,0,0]-qhat[0,0,1])*p[0,0] + (qhat[0,1,0]-qhat[0,1,1])*p[0,1] + 
                   (qhat[1,0,0]-qhat[1,0,1])*p[1,0] + (qhat[1,1,0]-qhat[1,1,1])*p[1,1] +
                    np.sum(qhat[:,:,1])
                   )
        unfairness_fpr = abs(fpr1*p[1,1] + (1-fpr1)*p[0,1] - fpr0*p[1,0] - (1-fpr0)*p[0,0])
        if (fp == 0):
            unfairness_tpr = abs(tpr1*p[1,1] + (1-tpr1)*p[0,1] - tpr0*p[1,0] - (1-tpr0)*p[0,0])
        if (fp == 1):
            unfairness_tpr = 0
        unftilde = max(unfairness_fpr, unfairness_tpr)
        return(errtilde, unftilde)

    def postproc_label(Yhat, A, p):
        Ytilde = np.random.binomial( 1, p[ Yhat.astype(int).tolist(), A.values.reshape((1,len(Yhat))).tolist()[0] ] )
        return(Ytilde)
    
    def qhat(Yhat, A, Y):
        temp_df = pd.DataFrame( np.column_stack((np.array(Yhat), np.array(A), np.array(Y))), columns = ["Yhat", "A", "Y"])
        qhat = np.empty(shape=(2,2,2))
        for yhat in [0,1]:
            for a in [0,1]:
                for y in [0,1]:
                    qhat[yhat, a, y] = np.mean( (temp_df.Yhat == yhat) & (temp_df.A == a) & (temp_df.Y == y) )
        return(qhat)
    
    def rates(q):
        fpr0 = q[1,0,0]/(q[1,0,0] + q[0,0,0])
        fpr1 = q[1,1,0]/(q[1,1,0] + q[0,1,0])
        tpr0 = q[1,0,1]/(q[1,0,1] + q[0,0,1])
        tpr1 = q[1,1,1]/(q[1,1,1] + q[0,1,1])
        return [fpr0, fpr1, tpr0, tpr1]
    
    def error(Yhat, Y):
        err = np.mean(Yhat != Y)
        return(err)
    
    def unfairness(Yhat, A, Y, fp):
        qhat = dp_postproc.qhat(Yhat, A, Y)
        rates = dp_postproc.rates(qhat)
        unfairness_fpr = abs(rates[0]-rates[1])
        if (fp == 0):
            unfairness_tpr = abs(rates[2]-rates[3])
        if (fp == 1):
            unfairness_tpr = 0
        return max(unfairness_fpr, unfairness_tpr)