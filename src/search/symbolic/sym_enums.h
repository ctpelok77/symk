#ifndef SYMBOLIC_SYM_ENUMS_H
#define SYMBOLIC_SYM_ENUMS_H

#include <iostream>
#include <string>
#include <vector>

// Auxiliar file to declare all enumerate values Each enumerate has:
// its definiton, ostream << operator and an array with representattive
// strings. The order of the values in the enumerate must correspond
// with the order in the xxxValues vector

namespace symbolic {
enum class MutexType {
  MUTEX_NOT,
  MUTEX_AND,
  MUTEX_EDELETION,
  /*MUTEX_RESTRICT, MUTEX_NPAND, MUTEX_CONSTRAIN, MUTEX_LICOMP*/
};
std::ostream &operator<<(std::ostream &os, const MutexType &m);
extern const std::vector<std::string> MutexTypeValues;

enum class Dir { FW, BW, BIDIR };
std::ostream &operator<<(std::ostream &os, const Dir &dir);
extern const std::vector<std::string> DirValues;

} // namespace symbolic
#endif