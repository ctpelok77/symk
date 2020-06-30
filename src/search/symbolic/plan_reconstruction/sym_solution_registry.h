#ifndef SYMBOLIC_PLAN_RECONSTRUCTION_SYM_SOLUTION_REGISTRY_H
#define SYMBOLIC_PLAN_RECONSTRUCTION_SYM_SOLUTION_REGISTRY_H

#include "../../plan_manager.h"
#include "../../state_registry.h"
#include "../../task_proxy.h"
#include "../plan_selection/plan_database.h"
#include "../sym_variables.h"
#include "../transition_relation.h"
#include "sym_solution_cut.h"

namespace symbolic {
class UniformCostSearch;
class ClosedList;

class SymSolutionRegistry {
protected:
  bool single_solution;

  std::vector<SymSolutionCut> sym_cuts; // sorted in ascending order!

  std::shared_ptr<SymVariables> sym_vars;
  UniformCostSearch *fw_search;
  UniformCostSearch *bw_search;
  std::shared_ptr<PlanDataBase> plan_data_base;
  std::map<int, std::vector<TransitionRelation>> trs;
  int plan_cost_bound;

  bool task_has_zero_costs() const { return trs.count(0) > 0; }

  BDD get_resulting_state(const Plan &plan) const;

  void reconstruct_plans(const SymSolutionCut &cut);

  void add_plan(const Plan &plan) const;

  // Extracts all plans by a DFS, we copy the current plan suffix by every
  // recusive call which is why we don't use any reference for plan
  // BID: After reconstruction of the forward part we reverse the plan and
  // call extract_all_plans in bw direction which completes the plan
  // After completing a plan we store it in found plans!
  void extract_all_plans(SymSolutionCut &sym_cut, bool fw, Plan plan);

  void extract_all_cost_plans(SymSolutionCut &sym_cut, bool fw, Plan &plan);
  void extract_all_zero_plans(SymSolutionCut &sym_cut, bool fw, Plan &plan);

  // Return wether a zero cost reconstruction step was necessary
  bool reconstruct_zero_action(SymSolutionCut &sym_cut, bool fw,
                               std::shared_ptr<ClosedList> closed,
                               const Plan &plan);
  bool reconstruct_cost_action(SymSolutionCut &sym_cut, bool fw,
                               std::shared_ptr<ClosedList> closed,
                               const Plan &plan);

public:
  SymSolutionRegistry();

  void init(std::shared_ptr<SymVariables> sym_vars,
            UniformCostSearch *fwd_search, UniformCostSearch *bwd_search,
            std::shared_ptr<PlanDataBase> plan_data_base, bool single_solution);

  void register_solution(const SymSolutionCut &solution);
  void construct_cheaper_solutions(int bound);

  bool found_all_plans() const {
    return plan_data_base && plan_data_base->found_enough_plans();
  }

  int get_num_found_plans() const {
    if (plan_data_base == nullptr) {
      return 0;
    }
    return plan_data_base->get_num_accepted_plans();
  }

  BDD get_states_on_goal_paths() const {
    return plan_data_base->get_states_accepted_goal_path();
  }
};
} // namespace symbolic

#endif