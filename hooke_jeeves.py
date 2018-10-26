def rosenbrock(x):
    '''
        ## Rosenbrocks classic parabolic valley ("banana") function
    '''
    a = x[0]
    b = x[1]
    return ((1.0 - a)**2) + (100.0 * (b - (a**2))**2)

def _hooke_best_nearby(f, delta, point, prevbest):
    '''
        ## given a point, look for a better one nearby
        one coord at a time
        
        f is a function that takes a list of floats (of the same length as point) as an input
        args is a dict of any additional arguments to pass to f
        delta, and point are same-length lists of floats
        prevbest is a float
        
        point and delta are both modified by the function
    '''
    z = [x for x in point]
    minf = prevbest
    ftmp = 0.0
    
    fev = 0
    
    for i in range(len(point)):
        #see if moving point in the positive delta direction decreases the 
        z[i] = point[i] + delta[i]
        ftmp = f(z)
        fev += 1
        if ftmp < minf:
            minf = ftmp
        else:
            #if not, try moving it in the other direction
            delta[i] = -delta[i]
            z[i] = point[i] + delta[i]
            ftmp = f(z)
            fev += 1
            if ftmp < minf:
                minf = ftmp
            else:
                #if moving the point in both delta directions result in no improvement, then just keep the point where it is
                z[i] = point[i]

    for i in range(len(z)):
        point[i] = z[i]
    return (minf, fev)
                
        
def hooke(f, startpt, rho=0.5, epsilon=1E-6, itermax=5000):
    result = dict()
    result['success'] = True
    result['message'] = 'success'
    
    delta = [0.0] * len(startpt)
    xbefore = [x for x in startpt]
    newx = [x for x in startpt]
    endpt = [0.0] * len(startpt)
    
    fmin = None
    nfev = 0
    iters = 0
    
    try:
        for i in range(len(startpt)):
            delta[i] = abs(startpt[i] * rho)
            if (delta[i] == 0.0):
                # we always want a non-zero delta because otherwise we'd just be checking the same point over and over
                # and wouldn't find a minimum
                delta[i] = rho

        steplength = rho

        fbefore = f(newx)
        nfev += 1
        
        newf = fbefore
        fmin = newf
        while ((iters < itermax) and (steplength > epsilon)):
            iters += 1
            #print "after %5d , f(x) = %.4le at" % (funevals, fbefore)
            
    #        for j in range(len(startpt)):
                #print "   x[%2d] = %4le" % (j, xbefore[j])
    #            pass
            
            ##/* find best new point, one coord at a time */
            newx = [x for x in xbefore]
            (newf, evals) = _hooke_best_nearby(f, delta, newx, fbefore)
            nfev += evals
            ##/* if we made some improvements, pursue that direction */
            keep = 1
            while ((newf < fbefore) and (keep == 1)):
                fmin = newf
                for i in range(len(startpt)):
                    ##/* firstly, arrange the sign of delta[] */
                    if newx[i] <= xbefore[i]:
                        delta[i] = -abs(delta[i])
                    else:
                        delta[i] = abs(delta[i])
                    ## /* now, move further in this direction */
                    tmp = xbefore[i]
                    xbefore[i] = newx[i]
                    newx[i] = newx[i] + newx[i] - tmp
                fbefore = newf
                (newf, evals) = _hooke_best_nearby(f, delta, newx, fbefore)
                nfev += evals
                ##/* if the further (optimistic) move was bad.... */
                if (newf >= fbefore):
                    break
                
                ## /* make sure that the differences between the new */
                ## /* and the old points are due to actual */
                ## /* displacements; beware of roundoff errors that */
                ## /* might cause newf < fbefore */
                keep = 0
                for i in range(len(startpt)):
                    keep = 1
                    if ( abs(newx[i] - xbefore[i]) > (0.5 * abs(delta[i])) ):
                        break
                    else:
                        keep = 0
            if ((steplength >= epsilon) and (newf >= fbefore)):
                steplength = steplength * rho
                delta = [x * rho for x in delta]
        for x in range(len(xbefore)):
            endpt[x] = xbefore[x]
    except Exception as e:
        result['success'] = False
        result['message'] = str(e)
    finally:
        result['nit'] = iters
        result['fevals'] = nfev
        result['fun'] = fmin
        result['x'] = endpt
    
    return result

def _point_in_bounds(point, bounds):
    '''
        shifts the point so it is within the given bounds
    '''
    for i in range(len(point)):
        if point[i] < bounds[i][0]:
            point[i] = bounds[i][0]
        elif point[i] > bounds[i][1]:
            point[i] = bounds[i][1]

def _is_point_in_bounds(point, bounds):
    '''
        true if the point is in the bounds, else false
    '''
    out = True
    for i in range(len(point)):
        if point[i] < bounds[i][0]:
            out = False
        elif point[i] > bounds[i][1]:
            out = False
    return out

def _bounded_func(f,bounds):
    '''
        returns a function that behaves like f except that it returns inf if the requested point is out of bounds.
    '''
    
    def func(point):
        out = None
        if _is_point_in_bounds(point,bounds):
            out = f(point)
        else:
            out = float('inf')
        return out

    return func
    
def hooke_bounded(f, startpt, bounds=None, rho=0.5, epsilon=1E-6, itermax=5000):
    
    #convert the input bounds to floats
    if bounds is None:
        # if bounds is none, make it none for all (it will be converted to below)
        bounds = [[None,None] for x in startpt]
    else:
        bounds = [[x[0],x[1]] for x in bounds] #make it so it wont update the original
    for bound in bounds:
        if bound[0] is None:
            bound[0] = float('-inf')
        else:
            bound[0] = float(bound[0])
        if bound[1] is None:
            bound[1] = float('inf')
        else:
            bound[1] = float(bound[1])
    
    startpt = [x for x in startpt] #make it so it wont update the original
    _point_in_bounds(startpt, bounds) #shunt the startpoint into the bounds
    
    func = _bounded_func(f,bounds) #wrap the function in the boundser
    
    #excecute the Hooke and Jeeves algorithm like normal, but with the bounded function
    return hooke(func, startpt, rho=rho, epsilon=epsilon, itermax=itermax)
    

def main():
	w_in = 1
	x_in = 1
	y_in = 1
	z_in = 1
    start = [w_in,x_in,y_in,z_in]
    res = hooke(rosenbrock, start, rho=0.5)
    res2 = hooke_bounded(rosenbrock, start, bounds=((0,3),(0,10)), rho=0.5)
    print start
    print res
    print res2
if __name__ == "__main__":
    main()