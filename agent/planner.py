
import numpy as np
import utils

class Planner(object):

    def __init__(self, num_primitives, num_actions, max_num_features):
        
        self.num_primitives = num_primitives
        self.num_actions = num_actions
        self.action = np.zeros((num_actions,1))
        
        self.goal = np.zeros((max_num_features, 1))
        self.debug = False


    def step(self, model, n_features):
      
        #print 'self.goal before-beginning', self.goal.ravel()
        self.goal *= 1 - model.feature_activity
        #self.goal -= np.minimum(model.feature_activity, self.goal)
        #print 'self.goal before-middle', self.goal.ravel()
        self.GOAL_DECAY_RATE = 0.1
        self.goal *= 1 - self.GOAL_DECAY_RATE
        #print 'self.goal before-end', self.goal.ravel()

        self.debug = False
        if np.random.random_sample() < 0.0:
            self.debug = True
            
        if self.debug:
            print 'new iteration ======================================================================='
            print 'model.feature_activity', model.feature_activity[:n_features,:].ravel()
            print 'self.goal', self.goal[np.nonzero(self.goal)[0],:].ravel(), \
                                   np.nonzero(self.goal)[0].ravel()
        

        #self.deliberate(model, attended_feature, n_features)  
        self.deliberate(model, n_features)  
        
        #reaction = self.react(model)
        
        #self.goal = reaction + excitation - inhibition
        #self.goal = np.maximum(self.goal, 0.)
        #self.goal = np.minimum(self.goal, 1.)
        
        #print reaction.ravel(), 'reaction'
        #print excitation.ravel(), 'excitation'
        #print inhibition.ravel(), 'inhibition'
        #print self.goal.ravel(), 'goal'
        
        #self.planner_salience = np.minimum(excitation + inhibition, 1.)


        """ Separate action goals from the rest of the goal """
        #self.action = np.sign(self.goal[self.num_primitives: self.num_primitives + self.num_actions,:])
        #print 'self.goal before', self.goal.ravel()
        self.goal[self.num_primitives: self.num_primitives + self.num_actions,:] = \
                np.sign(self.goal[self.num_primitives: self.num_primitives + self.num_actions,:])
        self.action = np.copy(self.goal[self.num_primitives: self.num_primitives + self.num_actions,:])
        #self.action = np.maximum(self.action, 0.)

        #print 'self.goal after', self.goal.ravel()
        #print 'self.action', self.action.ravel()
        #debug
        #self.goal = np.zeros(self.goal.shape)
        
        return self.action
            
            
    def deliberate(self, model, n_features):
        
        context_matches = (np.sum(model.context * model.feature_activity, axis=0)[np.newaxis,:]) ** 4
        match_indices = np.nonzero(context_matches)[1]
        #penalized_reward_value = model.reward_value  * (1 - model.reward_uncertainty ** 0.25)# - model.current_reward
        #penalized_reward_value = np.maximum(penalized_reward_value, 0)
        #reward_value_by_feature = utils.weighted_average(penalized_reward_value, 
        #        context_matches * model.cause / (model.reward_uncertainty + utils.EPSILON))
        
        estimated_reward_value = model.reward_value + model.reward_uncertainty * \
                    (np.random.random_sample(model.reward_uncertainty.shape) * 2 - 1)
        estimated_reward_value = np.maximum(estimated_reward_value, 0)
        estimated_reward_value = np.minimum(estimated_reward_value, 1)
        reward_value_by_feature = utils.weighted_average(estimated_reward_value, 
                context_matches * model.cause / (model.reward_uncertainty + utils.EPSILON))
        #print 'model.reward_uncertainty', model.reward_uncertainty
        #print 'model.reward_value ', model.reward_value 
        #print 'penalized_reward_value', penalized_reward_value
        #print 'reward_value_by_feature', reward_value_by_feature
        
        #reward_value_by_feature = utils.weighted_average(model.reward_value, 
        #        context_matches * model.cause / (model.reward_uncertainty + utils.EPSILON))
        
        # TODO: 
        # change from max goal value to a summation of them? bounded sum?
        
        goal_jitter = utils.EPSILON * np.random.random_sample(model.effect.shape)
        '''goal_indices = np.argmax((model.effect - model.effect_uncertainty) * 
                                 self.goal + goal_jitter, axis=0)
        transition_indices = np.arange(model.effect.shape[1])
        goal_value_by_transition = (model.effect * self.goal)[goal_indices,transition_indices] 
        goal_value_uncertainty_by_transition = \
                        (model.effect_uncertainty * self.goal)[goal_indices,transition_indices]
        penalized_goal_value = goal_value_by_transition * (1 - goal_value_uncertainty_by_transition ** 0.25)
        penalized_goal_value = np.maximum(penalized_goal_value, 0)
        goal_value_by_feature = utils.weighted_average(penalized_goal_value, 
                context_matches * model.cause / (goal_value_uncertainty_by_transition + utils.EPSILON))
        '''
        estimated_effect = model.effect + model.effect_uncertainty * \
                    (np.random.random_sample(model.effect_uncertainty.shape) * 2 - 1)
        estimated_effect = np.maximum(estimated_effect, 0)
        estimated_effect = np.minimum(estimated_effect, 1)
        """ Bounded sum over all the goal value amassed in a given transition """
        goal_value_by_transition = utils.map_inf_to_one(np.sum(utils.map_one_to_inf(
                            estimated_effect * (self.goal + goal_jitter)), axis=0)[np.newaxis,:])    
        goal_value_uncertainty_by_transition = utils.map_inf_to_one(np.sum(utils.map_one_to_inf(
                            model.effect_uncertainty * (self.goal + goal_jitter)), axis=0)[np.newaxis,:])
        goal_value_by_feature = utils.weighted_average(goal_value_by_transition, 
                context_matches * model.cause / (goal_value_uncertainty_by_transition + utils.EPSILON))
                 
        #goal_value_by_feature = utils.weighted_average(goal_value_by_transition, 
        #        context_matches * model.cause / (goal_value_uncertainty_by_transition + utils.EPSILON))
         
        #value_by_feature = utils.map_inf_to_one(utils.map_one_to_inf(reward_value_by_feature) + 
        #                                        utils.map_one_to_inf(goal_value_by_feature))
        
        count_by_feature = utils.weighted_average(model.count, context_matches * model.cause)
        self.EXPLORATION_FACTOR = 1.
        #exploration_vote = self.EXPLORATION_FACTOR / (count_by_feature + 1)
        #exploration_vote = 1. / (count_by_feature + 1)
        exploration_vote = self.EXPLORATION_FACTOR * (1 - model.current_reward) / \
            (n_features * (count_by_feature + 1) * np.random.random_sample(reward_value_by_feature.shape))
        exploration_vote = np.minimum(exploration_vote, 1.)
        exploration_vote[n_features:] = 0.
        
        #total_vote = utils.map_inf_to_one(utils.map_one_to_inf(exploration_vote) + 
        #                                  utils.map_one_to_inf(value_by_feature))
        total_vote = reward_value_by_feature + goal_value_by_feature + exploration_vote
        bounded_total_vote = utils.map_inf_to_one(utils.map_one_to_inf(reward_value_by_feature) + 
                                          utils.map_one_to_inf(goal_value_by_feature) + 
                                          utils.map_one_to_inf(exploration_vote))
        '''
        total_vote = reward_value_by_feature + goal_value_by_feature
        bounded_total_vote = utils.map_inf_to_one(utils.map_one_to_inf(reward_value_by_feature) + 
                                          utils.map_one_to_inf(goal_value_by_feature))
        
        total_vote = reward_value_by_feature + exploration_vote
        bounded_total_vote = utils.map_inf_to_one(utils.map_one_to_inf(reward_value_by_feature) + 
                                         utils.map_one_to_inf(exploration_vote))
        ''' 
        adjusted_vote = total_vote * (1 - self.goal)
        '''adjusted_vote = np.maximum(adjusted_vote, utils.EPSILON)
        
        #adjusted_vote_power = adjusted_vote ** n_features
        #adjusted_vote_power = np.sign(adjusted_vote) * np.abs(adjusted_vote) ** n_features
        adjusted_vote_power = np.sign(adjusted_vote) * np.abs(adjusted_vote) ** 10
        #adjusted_vote_power = adjusted_vote ** (n_features ** 0.5)
        cumulative_vote = np.cumsum(adjusted_vote_power, axis=0) / np.sum(adjusted_vote_power, axis=0)
        new_goal_feature = np.nonzero(np.random.random_sample() < cumulative_vote)[0][0]
        self.goal[new_goal_feature, :] = np.maximum(bounded_total_vote[new_goal_feature, :], 
                                                    self.goal[new_goal_feature, :])
        '''
        new_goal_feature = np.argmax(adjusted_vote, axis=0)
        self.goal[new_goal_feature, :] = np.maximum(bounded_total_vote[new_goal_feature, :], 
                                                    self.goal[new_goal_feature, :])
        
        #self.goal[new_goal_feature, :] = np.max((reward_value_by_feature[new_goal_feature, :],
        #                                         goal_value_by_feature[new_goal_feature, :],
        #                                         exploration_vote[new_goal_feature, :]))
        #self.goal[new_goal_feature, :] = np.max((reward_value_by_feature[new_goal_feature, :],
        #                                         exploration_vote[new_goal_feature, :]))
        #self.goal[new_goal_feature, :] = np.minimum(self.goal[new_goal_feature, :], 1.)
        #self.goal[new_goal_feature, :] = np.minimum(self.goal[new_goal_feature, :], 1 - model.current_reward)
        
        #print 'adjusted_vote', adjusted_vote.ravel()
        
        """ TODO: update the transition (if any) associated with the context and goal """
        
        if self.debug:
            #if np.random.random_sample() < 0.0:
            print 'context_matches', match_indices.ravel()
            print 'model.context', model.context[:n_features,match_indices]
            print 'model.cause', model.cause[:n_features,match_indices]        
            print 'model.effect', model.effect[:n_features,match_indices]        
            print 'model.effect_uncertainty', model.effect_uncertainty[:n_features,match_indices]   
            print 'model.reward',  model.reward_value[:,match_indices]     
            print 'model.reward_uncertainty',  model.reward_uncertainty[:,match_indices]     
            print 'estimated_reward_value', estimated_reward_value[:,match_indices]
            print 'model.feature_activity', model.feature_activity[:n_features,:].ravel()
            print 'estimated_effect', estimated_effect[:n_features,match_indices]
            print 'goal_value_by_transition', goal_value_by_transition[:,match_indices].ravel()
            print 'goal_value_uncertainty_by_transition', goal_value_uncertainty_by_transition[:,match_indices].ravel()
            print 'reward_value_by_feature', reward_value_by_feature.ravel()
            print 'goal_value_by_feature', goal_value_by_feature.ravel()
            print 'model.current_reward', model.current_reward
            
            #print 'count_by_feature', count_by_feature.ravel()
            print 'exploration_vote', exploration_vote.ravel()
            print 'total_vote', total_vote.ravel()
            print 'adjusted_vote', adjusted_vote.ravel()
            #print 'adjusted_vote_power', adjusted_vote_power.ravel()
            #print 'cumulative_vote', cumulative_vote.ravel()
            print 'adjusted_vote[new_goal_feature, :]', adjusted_vote[new_goal_feature, :]
            print 'new_goal_feature', new_goal_feature
            print 'total_vote[new_goal_feature, :]', total_vote[new_goal_feature, :]
                        
            print 'self.goal', self.goal.ravel()
            
            relevant_transitions = np.where(model.cause[new_goal_feature, match_indices] > 0)[0]
            if relevant_transitions.size > 0:
                print 'relevant_transitions', relevant_transitions
                print 'relevant_model.context', model.context[:n_features,match_indices[relevant_transitions]]
                print 'relevant_model.cause', model.cause[:n_features,match_indices[relevant_transitions]]        
                print 'relevant_model.effect', model.effect[:n_features,match_indices[relevant_transitions]]        
                print 'relevant_model.effect_uncertainty', model.effect_uncertainty[:n_features,match_indices[relevant_transitions]]   
                print 'relevant_model.reward',  model.reward_value[:,match_indices[relevant_transitions]]     
                print 'relevant_model.reward_uncertainty',  model.reward_uncertainty[:,match_indices[relevant_transitions]]     

        return
    

    def react(self, model):
        '''predicted_action = model.prediction[self.num_primitives: 
                                             self.num_primitives + self.num_actions,:]
        prediction_uncertainty = model.prediction_uncertainty[self.num_primitives: 
                                             self.num_primitives + self.num_actions,:]
        #reaction_threshold =  np.maximum(predicted_action ** 0.5 - prediction_uncertainty, 0)
        #reaction_threshold =  predicted_action
        
        #reaction = np.zeros(reaction_threshold.shape)
        #reaction[np.nonzero(np.random.random_sample(reaction.shape) < reaction_threshold)] = 1.0
            
        reaction =  predicted_action - prediction_uncertainty
        '''
        prediction, prediction_uncertainty = model.predict_next_step()
        reaction = prediction - prediction_uncertainty
        """ TODO: try this instead ? """
        #reaction = prediction
        
        if np.random.random_sample() < 0: 
            #if np.max(reaction.ravel()) > 0.01:
            print 'prediction', predicted_action.ravel(), ' uncertainty', prediction_uncertainty.ravel()
            #print 'reaction_threshold', reaction_threshold.ravel()
            print 'reaction', reaction.ravel()
        
        return reaction
