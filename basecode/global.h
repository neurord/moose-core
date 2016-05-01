/**********************************************************************
** This program is part of 'MOOSE', the
** Messaging Object Oriented Simulation Environment,
** also known as GENESIS 3 base code.
**           copyright (C) 2003-2004 Upinder S. Bhalla. and NCBS
** It is made available under the terms of the
** GNU Lesser Public License version 2.1
** See the file COPYING.LIB for the full notice.
**********************************************************************/


#ifndef  __MOOSE_GLOBAL_INC_
#define  __MOOSE_GLOBAL_INC_

#include <ctime>
#include <map>
#include <sstream>


using namespace std;

#include <boost/random/mersenne_twister.hpp>
#include <boost/random/uniform_01.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/filesystem.hpp>

#include "../external/debug/print_function.hpp"

/**
 * @brief Global stringstream for message printing.
 */
extern stringstream errorSS;

/**
 * @brief Keep tracks of how many tests have been executed in moose.
 */
extern unsigned int totalTests;


/** @brief This macro prints the output of a test function onto console.  It
 * also keep track of index of the current test. The index of test is
 * automatically computed by increamenting the counter.
 */

#define TEST_BEGIN cout << endl << "Test(" << totalTests << "): " << SIMPLE_CURRENT_FUNCTION;
#define TEST_END totalTests++; \
    cout << std::right <<  setw(20) << "test of " << SIMPLE_CURRENT_FUNCTION << " finished."; 

/*-----------------------------------------------------------------------------
 *  Global functions in namespace moose
 *-----------------------------------------------------------------------------*/
#define MISSING_BRACKET_AT_END                  -1
#define EMPTY_PATH                              -2
#define SPACES_AT_THE_BEGINING                  -3
#define SPACES_AT_THE_END                       -4
#define SPACES_IN_BETWEEN                       -5
#define BAD_CHARACTER_IN_PATH                   -6


namespace moose
{
    namespace global {

        typedef boost::random::mt19937 rng_type_;
        typedef boost::random::uniform_01<double> distribution_type_;

        extern rng_type_ rng;
        extern distribution_type_ dist;

        /**
         * @brief A global seed for all RNGs in moose. When moose.seed( x ) is called,
         * this variable is set. Other's RNGs (except muparser) uses this seed to
         * initialize them. By default it is initialized by random_device (see
         * global.cpp).
         */
        extern int __rng_seed__;

        /**
         * @brief Fix a path. For testing purpose.
         *
         * @param path Path as string.
         *
         * @return  A fixed path.
         */
        string fixPath(string path);

        /**
         * @brief Checks if given path is correct. 
         * If not, return false and error-code as well.
         *
         * @param path Path name.
         *
         * @return 0 if path is all-right. Negative number if path is not OK.
         */
        int checkPath( const string& path );

        /** @brief Append pathB to pathA and return the result. 
         *
         * If pathA does not have [indexs] at the end, append "[0]" to pathA and
         * then add pathB to it.  This version does not care if the result has '[0]'
         * at its end.
         *
         * @param pathA First path.  
         * @param pathB Second path.
         *
         * @return A string representing moose-path.
         */
        string joinPath(string pathA, string pathB);

        /**
         * @brief Seed seed for RNG.
         *
         * @param seed
         */
        void mtseed( unsigned int seed );

        /**
         * @brief Generate a random double between 0 and 1
         *
         * @return  A random number between 0 and 1.
         */
        double mtrand( void );

        /**
         * @brief Create a POSIX compatible path from a given string.
         * Remove/replace bad characters.
         *
         * @param path
         */
        string createPosixPath( string path );

        /**
         * @brief Convert a given value to string.
         *
         * @tparam T
         * @param x
         *
         * @return  String representation
         */
        template<typename T>
        string toString( T x )
        {
            return boost::lexical_cast<string>( x );
        }

        /**
         * @brief Create directory, recursively.
         *
         * @param path
         */
        void createDirs( boost::filesystem::path path );
    }
}

#endif   /* ----- #ifndef __MOOSE_GLOBAL_INC_  ----- */
