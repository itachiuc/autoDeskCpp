#include <string>
#include <cassert>
#include <cctype>
#include <algorithm>

/**
 * Reverses each "word" (contiguous sequence of alphanumeric characters)
 * in-place, leaving all other characters (spaces, punctuation) untouched
 * and in their original positions.
 *
 * Example: "String; 2be reversed..." -> "gnirtS; eb2 desrever..."
 */
 
std::string reverse_words(const std::string& str) {
    std::string result = str;
    size_t i = 0;

    while (i < result.size()) {
        if (std::isalnum(result[i])) {
            // Mark the start of a word, scan to find its end
            size_t word_start = i;
            while (i < result.size() && std::isalnum(result[i])) {
                ++i;
            }
            // Reverse just this word segment in-place
            std::reverse(result.begin() + word_start, result.begin() + i);
        } else {
            ++i;
        }
    }

    return result;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void run_tests() {
    // Provided requirement
    assert(reverse_words("String; 2be reversed...") == "gnirtS; eb2 desrever...");

    // Empty string
    assert(reverse_words("") == "");

    // Single character word
    assert(reverse_words("a") == "a");

    // Only non-word characters — nothing should change
    assert(reverse_words("... !!!") == "... !!!");

    // Single word, no punctuation
    assert(reverse_words("hello") == "olleh");

    // Multiple words separated by spaces
    assert(reverse_words("hello world") == "olleh dlrow");

    // Numbers are part of words
    assert(reverse_words("abc123 456def") == "321cba fed654");

    // Punctuation between words stays in place
    assert(reverse_words("one,two.three") == "eno,owt.eerht");

    // Leading and trailing punctuation
    assert(reverse_words("...hello...") == "...olleh...");

    // Already reversed word
    assert(reverse_words("olleh") == "hello");

    // Mixed alphanumeric words
    assert(reverse_words("a1b2 c3d4") == "2b1a 4d3c");

    // Multiple spaces between words
    assert(reverse_words("hi   there") == "ih   ereht");
}

int main() {
    run_tests();
    return 0;
}