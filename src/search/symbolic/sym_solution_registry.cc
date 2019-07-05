#include "sym_solution_registry.h"
#include "../tasks/root_task.h"
#include "sym_plan_reconstruction.h"

namespace symbolic {

    SymSolutionRegistry::SymSolutionRegistry(int target_num_plans)
    : plan_reconstructor(nullptr), num_target_plans(target_num_plans),
    relevant_task(*tasks::g_root_task), state_registry(nullptr),
    sym_vars(nullptr), plan_cost_bound(-1) {
    }

    void SymSolutionRegistry::init(std::shared_ptr<SymVariables> sym_vars, UnidirectionalSearch* fwd_search, UnidirectionalSearch* bwd_search) {
        this->sym_vars = sym_vars;
        state_registry = std::make_shared<StateRegistry>(relevant_task),
                states_on_goal_paths = sym_vars->zeroBDD();
        plan_reconstructor = std::make_shared<PlanReconstructor>(fwd_search, bwd_search, sym_vars, state_registry);
    }

    void SymSolutionRegistry::register_solution(const SymSolutionCut &solution) {

        SymSolutionCut new_cut(solution.get_g(), solution.get_h(), solution.get_cut());
        // std::cout << "\nregister " << new_cut << std::endl;

        bool merged = false;
        size_t pos = 0;
        for (; pos < sym_cuts.size(); pos++) {
            // A cut with same g and h values exist!
            if (sym_cuts[pos] == new_cut) {
                sym_cuts[pos].merge(new_cut);
                merged = true;
                break;
            }
            if (sym_cuts[pos] > new_cut) {
                break;
            }
        }
        if (!merged) {
            sym_cuts.insert(sym_cuts.begin() + pos, new_cut);
        }
    }

    void SymSolutionRegistry::construct_cheaper_solutions(int bound) {
        /*std::cout << "\nReconstruction bound: " << bound << std::endl;
        for (auto& cut : sym_cuts) {
            std::cout << cut << std::endl;
        }*/

        bool bound_used = false;
        int min_plan_bound = std::numeric_limits<int>::max();
        while (sym_cuts.size() > 0 && sym_cuts.at(0).get_f() < bound &&
                !found_all_plans()) {
            // std::cout << "Reconsturcting!" << plan_cost_bound << std::endl;
            // Ignore all cuts with costs smaller than the bound we already reconstructed
            if (sym_cuts.at(0).get_f() < plan_cost_bound) {
                sym_cuts.erase(sym_cuts.begin());
            } else {
                BDD goal_path_states;
                num_found_plans += plan_reconstructor->reconstruct_plans(sym_cuts[0], missing_plans(), goal_path_states);
                states_on_goal_paths += goal_path_states;
                min_plan_bound = std::min(min_plan_bound, sym_cuts.at(0).get_f());
                bound_used = true;
                sym_cuts.erase(sym_cuts.begin());
            }
        }

        if (bound_used) {
            plan_cost_bound = min_plan_bound;
        }

    }
} // namespace symbolic
