# -*- coding: utf-8 -*
"""
Keyboard maps for the Sage Notebook

AUTHORS:
    -- Tom Boothby
    -- William Stein
"""

#############################################################################
#       Copyright (C) 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################
from __future__ import absolute_import


"""
The functions below return a block of javascript code that defines
global variables for every key that we could think of that works in
(almost) all systems.  Keys intentionally not captured are escape,
insert, delete, and F1-F12.  Support for the capture of ctrl, alt,
and shift is spotty; however, checking for this is necessary for
proper behavior in IE.

This file contains keyboard layouts for the following systems:
Firefox 1.5 windows, mac, linux
Opera 9 windows, mac, linux (linux only tested on opera 8)
IE 6 windows
Safari
Konqueror

We are deaf to the complaints of users of the following systems:
AOL
IE mac
LYNX / other command line browsers (Sage has a command line interface!)
the browser your cousin wrote for your sister's birthday

If you think that your browser deserves support, go to the following page:

http://sage.math.washington.edu/home/boothby/modular.old/www/keys_capture.html

and follow the directions you see there.  Copy the output, and email
it to boothby@u.washington.edu
"""

def get_keyboard(s):
    # keyboard_map is a dictionary defined at the bottom of this
    # file that maps os/browser codes to functions that give the
    # corresponding keymaps.
    if keyboard_map.has_key(s):
        codes = keyboard_map[s]()
    else:
        # Default in case something goes wrong.  This should
        # never get called.
        codes = keyboard_map['mm']()

    defaults = {'KEY_CTRLENTER':'KEY_ENTER'}

    # We now add in each default keycode if it isn't already present.
    # The point of this is that it allows us to easily alias keys to
    # predefined keys, but doesn't overwrite anything.
    for key, val in defaults.iteritems():
        if '%s =' % key not in codes:
            codes += '\nvar %s = %s;' % (key,val)

    return codes.strip()


def keyboard_moz_win():
    return """
var KEY_SHIFT = "16,16!";
var KEY_CTRL = "20,20";
var KEY_ALT = "18,18";
var KEY_ESC = "27,0";
var KEY_HOME = "36,0";
var KEY_END = "35,0";
var KEY_PGUP = "33,0";
var KEY_PGDN = "34,0";
var KEY_BKSPC = "8,8";
var KEY_SPC = "0,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,0";
var KEY_Q = "0,113";
var KEY_W = "0,119";
var KEY_E = "0,101";
var KEY_R = "0,114";
var KEY_T = "0,116";
var KEY_Y = "0,121";
var KEY_U = "0,117";
var KEY_I = "0,105";
var KEY_O = "0,111";
var KEY_P = "0,112";
var KEY_QQ = "0,81!";
var KEY_WW = "0,87!";
var KEY_EE = "0,69!";
var KEY_RR = "0,82!";
var KEY_TT = "0,84!";
var KEY_YY = "0,89!";
var KEY_UU = "0,85!";
var KEY_II = "0,73!";
var KEY_OO = "0,79!";
var KEY_PP = "0,80!";
var KEY_A = "0,97";
var KEY_S = "0,115";
var KEY_D = "0,100";
var KEY_F = "0,102";
var KEY_G = "0,103";
var KEY_H = "0,104";
var KEY_J = "0,106";
var KEY_K = "0,107";
var KEY_L = "0,108";
var KEY_AA = "0,65!";
var KEY_SS = "0,68!";
var KEY_DD = "0,70!";
var KEY_FF = "0,70!";
var KEY_GG = "0,71!";
var KEY_HH = "0,72!";
var KEY_JJ = "0,74!";
var KEY_KK = "0,75!";
var KEY_LL = "0,76!";
var KEY_Z = "0,122";
var KEY_X = "0,120";
var KEY_C = "0,99";
var KEY_V = "0,118";
var KEY_B = "0,98";
var KEY_N = "0,110";
var KEY_M = "0,109";
var KEY_ZZ = "0,90!";
var KEY_XX = "0,88!";
var KEY_CC = "0,67!";
var KEY_VV = "0,86!";
var KEY_BB = "0,66!";
var KEY_NN = "0,78!";
var KEY_MM = "0,77!";
var KEY_1 = "0,49";
var KEY_2 = "0,50";
var KEY_3 = "0,51";
var KEY_4 = "0,52";
var KEY_5 = "0,53";
var KEY_6 = "0,54";
var KEY_7 = "0,55";
var KEY_8 = "0,56";
var KEY_9 = "0,57";
var KEY_0 = "0,48";
var KEY_BANG = "0,33!";
var KEY_AT = "0,64!";
var KEY_HASH = "0,35!";
var KEY_DOLLAR = "0,36!";
var KEY_MOD = "0,37!";
var KEY_CARET = "0,94!";
var KEY_AMP = "0,38!";
var KEY_AST = "0,42!";
var KEY_LPAR = "0,40!";
var KEY_RPAR = "0,41!";
var KEY_MINUS = "0,45";
var KEY_UNDER = "0,95!";
var KEY_PLUS = "0,43!";
var KEY_EQ = "0,61";
var KEY_LBRACE = "0,123!";
var KEY_RBRACE = "0,125!";
var KEY_LBRACK = "0,91";
var KEY_RBRACK = "0,93";
var KEY_PIPE = "0,124!";
var KEY_SLASH = "0,92";
var KEY_COLON = "0,58!";
var KEY_SEMI = "0,59";
var KEY_QUOTE = "0,34!";
var KEY_APOS = "0,39";
var KEY_BSLASH = "191,0";
var KEY_QUEST = "191,0!";
var KEY_COMMA = "0,44";
var KEY_DOT = "0,46";
var KEY_TILDE = "0,126!";
var KEY_TICK = "0,96";
var KEY_LT = "0,60!";
var KEY_GT = "0,62!";
var KEY_LEFT = "37,0";
var KEY_UP = "38,0";
var KEY_RIGHT = "39,0";
var KEY_DOWN = "40,0";
    """



def keyboard_moz_lin():
    return """
var KEY_SHIFT = "16,16";
var KEY_CTRL = "17,17";
var KEY_ALT = "18,18";
var KEY_ESC = "27,0";
var KEY_HOME = "36,0";
var KEY_END = "35,0";
var KEY_PGUP = "33,0";
var KEY_PGDN = "34,0";
var KEY_BKSPC = "8,8";
var KEY_SPC = "0,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,0";
var KEY_Q = "0,113";
var KEY_W = "0,119";
var KEY_E = "0,101";
var KEY_R = "0,114";
var KEY_T = "0,116";
var KEY_Y = "0,121";
var KEY_U = "0,117";
var KEY_I = "0,105";
var KEY_O = "0,111";
var KEY_P = "0,112";
var KEY_QQ = "0,81!";
var KEY_WW = "0,87!";
var KEY_EE = "0,69!";
var KEY_RR = "0,82!";
var KEY_TT = "0,84!";
var KEY_YY = "0,89!";
var KEY_UU = "0,85!";
var KEY_II = "0,73!";
var KEY_OO = "0,79!";
var KEY_PP = "0,80!";
var KEY_A = "0,97";
var KEY_S = "0,115";
var KEY_D = "0,100";
var KEY_F = "0,102";
var KEY_G = "0,103";
var KEY_H = "0,104";
var KEY_J = "0,106";
var KEY_K = "0,107";
var KEY_L = "0,108";
var KEY_AA = "0,65!";
var KEY_SS = "0,83!";
var KEY_DD = "0,68!";
var KEY_FF = "0,70!";
var KEY_GG = "0,71!";
var KEY_HH = "0,72!";
var KEY_JJ = "0,74!";
var KEY_KK = "0,75!";
var KEY_LL = "0,76!";
var KEY_Z = "0,122";
var KEY_X = "0,120";
var KEY_C = "0,99";
var KEY_V = "0,118";
var KEY_B = "0,98";
var KEY_N = "0,110";
var KEY_M = "0,109";
var KEY_ZZ = "0,90!";
var KEY_XX = "0,88!";
var KEY_CC = "0,67!";
var KEY_VV = "0,86!";
var KEY_BB = "0,66!";
var KEY_NN = "0,78!";
var KEY_MM = "0,77!";
var KEY_1 = "0,49";
var KEY_2 = "0,50";
var KEY_3 = "0,51";
var KEY_4 = "0,52";
var KEY_5 = "0,53";
var KEY_6 = "0,54";
var KEY_7 = "0,55";
var KEY_8 = "0,56";
var KEY_9 = "0,57";
var KEY_0 = "0,48";
var KEY_BANG = "0,33!";
var KEY_AT = "0,64!";
var KEY_HASH = "0,35!";
var KEY_DOLLAR = "0,36!";
var KEY_MOD = "0,37!";
var KEY_CARET = "0,94!";
var KEY_AMP = "0,38!";
var KEY_AST = "0,42!";
var KEY_LPAR = "0,40!";
var KEY_RPAR = "0,41!";
var KEY_MINUS = "0,45";
var KEY_UNDER = "0,95!";
var KEY_PLUS = "0,43!";
var KEY_EQ = "0,61";
var KEY_LBRACE = "0,123!";
var KEY_RBRACE = "0,125!";
var KEY_LBRACK = "0,91";
var KEY_RBRACK = "0,93";
var KEY_PIPE = "0,124!";
var KEY_SLASH = "0,92";
var KEY_COLON = "0,58!";
var KEY_SEMI = "0,59";
var KEY_QUOTE = "0,34!";
var KEY_APOS = "0,39";
var KEY_BSLASH = "0,47";
var KEY_QUEST = "0,63!";
var KEY_COMMA = "0,44";
var KEY_DOT = "0,46";
var KEY_TILDE = "0,126!";
var KEY_TICK = "0,96";
var KEY_LT = "0,60!";
var KEY_GT = "0,62!";
var KEY_LEFT = "37,0";
var KEY_UP = "38,0";
var KEY_RIGHT = "39,0";
var KEY_DOWN = "40,0";
    """



def keyboard_moz_mac():
    return """
var KEY_SHIFT = "";
var KEY_CTRL = "";
var KEY_ALT = "";
var KEY_ESC = "27,0";
var KEY_HOME = "36,0";
var KEY_END = "35,0";
var KEY_PGUP = "33,0";
var KEY_PGDN = "34,0";
var KEY_BKSPC = "8,8";
var KEY_SPC = "0,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_CTRLENTER = "77,0";
var KEY_TAB = "9,0";
var KEY_Q = "0,113";
var KEY_W = "0,119";
var KEY_E = "0,101";
var KEY_R = "0,114";
var KEY_T = "0,116";
var KEY_Y = "0,121";
var KEY_U = "0,117";
var KEY_I = "0,105";
var KEY_O = "0,111";
var KEY_P = "0,112";
var KEY_QQ = "0,81!";
var KEY_WW = "0,87!";
var KEY_EE = "0,69!";
var KEY_RR = "0,82!";
var KEY_TT = "0,84!";
var KEY_YY = "0,89!";
var KEY_UU = "0,85!";
var KEY_II = "0,73!";
var KEY_OO = "0,79!";
var KEY_PP = "0,80!";
var KEY_A = "0,97";
var KEY_S = "0,115";
var KEY_D = "0,100";
var KEY_F = "0,102";
var KEY_G = "0,103";
var KEY_H = "0,104";
var KEY_J = "0,106";
var KEY_K = "0,107";
var KEY_L = "0,108";
var KEY_AA = "0,65!";
var KEY_SS = "0,83!";
var KEY_DD = "0,68!";
var KEY_FF = "0,70!";
var KEY_GG = "0,71!";
var KEY_HH = "0,72!";
var KEY_JJ = "0,74!";
var KEY_KK = "0,75!";
var KEY_LL = "0,76!";
var KEY_Z = "0,122";
var KEY_X = "0,120";
var KEY_C = "0,99";
var KEY_V = "0,118";
var KEY_B = "0,98";
var KEY_N = "0,110";
var KEY_M = "0,109";
var KEY_ZZ = "0,90!";
var KEY_XX = "0,88!";
var KEY_CC = "0,67!";
var KEY_VV = "0,86!";
var KEY_BB = "0,66!";
var KEY_NN = "0,78!";
var KEY_MM = "0,77!";
var KEY_1 = "0,49";
var KEY_2 = "0,50";
var KEY_3 = "0,51";
var KEY_4 = "0,52";
var KEY_5 = "0,53";
var KEY_6 = "0,54";
var KEY_7 = "0,55";
var KEY_8 = "0,56";
var KEY_9 = "0,57";
var KEY_0 = "0,48";
var KEY_BANG = "0,33!";
var KEY_AT = "0,64!";
var KEY_HASH = "0,35!";
var KEY_DOLLAR = "0,36!";
var KEY_MOD = "0,37!";
var KEY_CARET = "0,94!";
var KEY_AMP = "0,38!";
var KEY_AST = "0,42!";
var KEY_LPAR = "0,40!";
var KEY_RPAR = "0,41!";
var KEY_MINUS = "0,45";
var KEY_UNDER = "0,95!";
var KEY_PLUS = "0,43!";
var KEY_EQ = "0,61";
var KEY_LBRACE = "0,123!";
var KEY_RBRACE = "0,125!";
var KEY_LBRACK = "0,91";
var KEY_RBRACK = "0,93";
var KEY_PIPE = "0,124!";
var KEY_SLASH = "0,92";
var KEY_COLON = "0,58!";
var KEY_SEMI = "0,59";
var KEY_QUOTE = "0,34!";
var KEY_APOS = "0,39";
var KEY_BSLASH = "0,47";
var KEY_QUEST = "0,63!";
var KEY_COMMA = "0,44";
var KEY_DOT = "0,46";
var KEY_TILDE = "0,126!";
var KEY_TICK = "0,96";
var KEY_LT = "0,60!";
var KEY_GT = "0,62!";
var KEY_LEFT = "37,0";
var KEY_UP = "38,0";
var KEY_RIGHT = "39,0";
var KEY_DOWN = "40,0";
    """

def keyboard_op_win():
    return """
var KEY_SHIFT = "16,16!";
var KEY_CTRL = "20,20";
var KEY_ALT = "";
var KEY_ESC = "27,27";
var KEY_HOME = "36,36";
var KEY_END = "35,35";
var KEY_PGUP = "33,0";
var KEY_PGDN = "34,0";
var KEY_BKSPC = "8,8";
var KEY_SPC = "32,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,9";
var KEY_Q = "81,81";
var KEY_W = "87,87";
var KEY_E = "69,69";
var KEY_R = "82,82";
var KEY_T = "84,84";
var KEY_Y = "89,89";
var KEY_U = "85,85";
var KEY_I = "73,73";
var KEY_O = "79,79";
var KEY_P = "80,80";
var KEY_QQ = "113,113!";
var KEY_WW = "119,119!";
var KEY_EE = "101,101!";
var KEY_RR = "114,114!";
var KEY_TT = "116,116!";
var KEY_YY = "121,121!";
var KEY_UU = "117,117!";
var KEY_II = "105,105!";
var KEY_OO = "111,111!";
var KEY_PP = "112,112!";
var KEY_A = "65,65";
var KEY_S = "83,83";
var KEY_D = "68,68";
var KEY_F = "70,70";
var KEY_G = "71,71";
var KEY_H = "72,72";
var KEY_J = "74,74";
var KEY_K = "75,75";
var KEY_L = "76,76";
var KEY_AA = "97,97!";
var KEY_SS = "115,115!";
var KEY_DD = "100,100!";
var KEY_FF = "102,102!";
var KEY_GG = "103,103!";
var KEY_HH = "104,104!";
var KEY_JJ = "106,106!";
var KEY_KK = "107,107!";
var KEY_LL = "108,108!";
var KEY_Z = "90,90";
var KEY_X = "88,88";
var KEY_C = "67,67";
var KEY_V = "86,86";
var KEY_B = "66,66";
var KEY_N = "78,78";
var KEY_M = "77,77";
var KEY_ZZ = "122,122!";
var KEY_XX = "120,120!";
var KEY_CC = "99,99!";
var KEY_VV = "118,118!";
var KEY_BB = "98,98!";
var KEY_NN = "110,110!";
var KEY_MM = "109,109!";
var KEY_1 = "49,49";
var KEY_2 = "50,50";
var KEY_3 = "51,51";
var KEY_4 = "52,52";
var KEY_5 = "53,53";
var KEY_6 = "54,54";
var KEY_7 = "55,55";
var KEY_8 = "56,56";
var KEY_9 = "57,57";
var KEY_0 = "48,48";
var KEY_BANG = "33,33!";
var KEY_AT = "64,64!";
var KEY_HASH = "35,35!";
var KEY_DOLLAR = "36,36!";
var KEY_MOD = "37,37!";
var KEY_CARET = "94,94!";
var KEY_AMP = "38,38!";
var KEY_AST = "42,42!";
var KEY_LPAR = "40,40!";
var KEY_RPAR = "41,41!";
var KEY_MINUS = "45,45";
var KEY_UNDER = "95,95!";
var KEY_PLUS = "43,43!";
var KEY_EQ = "61,61";
var KEY_LBRACE = "123,123!";
var KEY_RBRACE = "125,125!";
var KEY_LBRACK = "91,91";
var KEY_RBRACK = "93,93";
var KEY_PIPE = "124,124!";
var KEY_SLASH = "92,92";
var KEY_COLON = "58,58!";
var KEY_SEMI = "59,59";
var KEY_QUOTE = "34,34!";
var KEY_APOS = "39,39";
var KEY_BSLASH = "47,47";
var KEY_QUEST = "63,63!";
var KEY_COMMA = "44,44";
var KEY_DOT = "46,46";
var KEY_TILDE = "126,126!";
var KEY_TICK = "96,96";
var KEY_LT = "60,60!";
var KEY_GT = "62,62!";
var KEY_LEFT = "37,0";
var KEY_UP = "38,0";
var KEY_RIGHT = "39,0";
var KEY_DOWN = "40,0";
    """




def keyboard_op_lin():
    return """
var KEY_SHIFT = "0,0";
var KEY_CTRL = "0,0";
var KEY_ALT = "0,0";
var KEY_ESC = "27,27";
var KEY_HOME = "";
var KEY_END = "";
var KEY_PGUP = "33,0";
var KEY_PGDN = "34,0";
var KEY_BKSPC = "8,8";
var KEY_SPC = "32,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,9";
var KEY_Q = "113,113";
var KEY_W = "119,119";
var KEY_E = "101,101";
var KEY_R = "114,114";
var KEY_T = "116,116";
var KEY_Y = "121,121";
var KEY_U = "117,117";
var KEY_I = "105,105";
var KEY_O = "111,111";
var KEY_P = "112,112";
var KEY_QQ = "81,81!";
var KEY_WW = "87,87!";
var KEY_EE = "69,69!";
var KEY_RR = "82,82!";
var KEY_TT = "84,84!";
var KEY_YY = "89,89!";
var KEY_UU = "85,85!";
var KEY_II = "73,73!";
var KEY_OO = "79,79!";
var KEY_PP = "80,80!";
var KEY_A = "97,97";
var KEY_S = "115,115";
var KEY_D = "100,100";
var KEY_F = "102,102";
var KEY_G = "103,103";
var KEY_H = "104,104";
var KEY_J = "106,106";
var KEY_K = "107,107";
var KEY_L = "108,108";
var KEY_AA = "65,65!";
var KEY_SS = "83,83!";
var KEY_DD = "68,68!";
var KEY_FF = "70,70!";
var KEY_GG = "71,71!";
var KEY_HH = "72,72!";
var KEY_JJ = "74,74!";
var KEY_KK = "75,75!";
var KEY_LL = "76,76!";
var KEY_Z = "122,122";
var KEY_X = "120,120";
var KEY_C = "99,99";
var KEY_V = "118,118";
var KEY_B = "98,98";
var KEY_N = "110,110";
var KEY_M = "109,109";
var KEY_ZZ = "90,90!";
var KEY_XX = "88,88!";
var KEY_CC = "67,67!";
var KEY_VV = "86,86!";
var KEY_BB = "66,66!";
var KEY_NN = "78,78!";
var KEY_MM = "77,77!";
var KEY_1 = "49,49";
var KEY_2 = "50,50";
var KEY_3 = "51,51";
var KEY_4 = "52,52";
var KEY_5 = "53,53";
var KEY_6 = "54,54";
var KEY_7 = "55,55";
var KEY_8 = "56,56";
var KEY_9 = "57,57";
var KEY_0 = "48,48";
var KEY_BANG = "33,33!";
var KEY_AT = "64,64!";
var KEY_HASH = "35,35!";
var KEY_DOLLAR = "36,36!";
var KEY_MOD = "37,37!";
var KEY_CARET = "94,94!";
var KEY_AMP = "38,38!";
var KEY_AST = "42,42!";
var KEY_LPAR = "40,40!";
var KEY_RPAR = "41,41!";
var KEY_MINUS = "45,45";
var KEY_UNDER = "95,95!";
var KEY_PLUS = "43,43!";
var KEY_EQ = "61,61";
var KEY_LBRACE = "123,123!";
var KEY_RBRACE = "125,125!";
var KEY_LBRACK = "91,91";
var KEY_RBRACK = "93,93";
var KEY_PIPE = "124,124!";
var KEY_SLASH = "92,92";
var KEY_COLON = "58,58!";
var KEY_SEMI = "59,59";
var KEY_QUOTE = "34,34!";
var KEY_APOS = "39,39";
var KEY_BSLASH = "47,47";
var KEY_QUEST = "63,63!";
var KEY_COMMA = "44,44";
var KEY_DOT = "46,46";
var KEY_TILDE = "126,126!";
var KEY_TICK = "96,96";
var KEY_LT = "60,60!";
var KEY_GT = "62,62!";
var KEY_LEFT = "37,0";
var KEY_UP = "38,0";
var KEY_RIGHT = "39,0";
var KEY_DOWN = "40,0";
    """

# You had var KEY_CTRL = "20,20";, but it"s ";0,0";
def keyboard_op_mac():
    return """
var KEY_SHIFT = "16,16";
var KEY_CTRL = "0,0";
var KEY_ALT = "18,18";
var KEY_ESC = "27,27";
var KEY_HOME = "36,36";
var KEY_END = "35,35";
var KEY_PGUP = "33,0";
var KEY_PGDN = "34,0";
var KEY_BKSPC = "8,8";
var KEY_SPC = "32,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,9";
var KEY_Q = "113,113";
var KEY_W = "119,119";
var KEY_E = "101,101";
var KEY_R = "114,114";
var KEY_T = "116,116";
var KEY_Y = "121,121";
var KEY_U = "117,117";
var KEY_I = "105,105";
var KEY_O = "111,111";
var KEY_P = "112,112";
var KEY_QQ = "81,81!";
var KEY_WW = "87,87!";
var KEY_EE = "69,69!";
var KEY_RR = "82,82!";
var KEY_TT = "84,84!";
var KEY_YY = "89,89!";
var KEY_UU = "85,85!";
var KEY_II = "73,73!";
var KEY_OO = "79,79!";
var KEY_PP = "80,80!";
var KEY_A = "97,97";
var KEY_S = "115,115";
var KEY_D = "100,100";
var KEY_F = "102,102";
var KEY_G = "103,103";
var KEY_H = "104,104";
var KEY_J = "106,106";
var KEY_K = "107,107";
var KEY_L = "108,108";
var KEY_AA = "65,65!";
var KEY_SS = "83,83!";
var KEY_DD = "68,68!";
var KEY_FF = "70,70!";
var KEY_GG = "71,71!";
var KEY_HH = "72,72!";
var KEY_JJ = "74,74!";
var KEY_KK = "75,75!";
var KEY_LL = "76,76!";
var KEY_Z = "122,122";
var KEY_X = "120,120";
var KEY_C = "99,99";
var KEY_V = "118,118";
var KEY_B = "98,98";
var KEY_N = "110,110";
var KEY_M = "109,109";
var KEY_ZZ = "90,90!";
var KEY_XX = "88,88!";
var KEY_CC = "67,67!";
var KEY_VV = "86,86!";
var KEY_BB = "66,66!";
var KEY_NN = "78,78!";
var KEY_MM = "77,77!";
var KEY_1 = "49,49";
var KEY_2 = "50,50";
var KEY_3 = "51,51";
var KEY_4 = "52,52";
var KEY_5 = "53,53";
var KEY_6 = "54,54";
var KEY_7 = "55,55";
var KEY_8 = "56,56";
var KEY_9 = "57,57";
var KEY_0 = "48,48";
var KEY_BANG = "33,33!";
var KEY_AT = "64,64!";
var KEY_HASH = "35,35!";
var KEY_DOLLAR = "36,36!";
var KEY_MOD = "37,37!";
var KEY_CARET = "94,94!";
var KEY_AMP = "38,38!";
var KEY_AST = "42,42!";
var KEY_LPAR = "40,40!";
var KEY_RPAR = "41,41!";
var KEY_MINUS = "45,45";
var KEY_UNDER = "95,95!";
var KEY_PLUS = "43,43!";
var KEY_EQ = "61,61";
var KEY_LBRACE = "123,123!";
var KEY_RBRACE = "125,125!";
var KEY_LBRACK = "91,91";
var KEY_RBRACK = "93,93";
var KEY_PIPE = "124,124!";
var KEY_SLASH = "92,92";
var KEY_COLON = "58,58!";
var KEY_SEMI = "59,59";
var KEY_QUOTE = "34,34!";
var KEY_APOS = "39,39";
var KEY_BSLASH = "47,47";
var KEY_QUEST = "63,63!";
var KEY_COMMA = "44,44";
var KEY_DOT = "46,46";
var KEY_TILDE = "126,126!";
var KEY_TICK = "96,96";
var KEY_LT = "60,60!";
var KEY_GT = "62,62!";
var KEY_LEFT = "37,0";
var KEY_UP = "38,0";
var KEY_RIGHT = "39,0";
var KEY_DOWN = "40,0";
    """

def keyboard_saf_mac():
    return """
var KEY_SHIFT = "";
var KEY_CTRL = "";
var KEY_ALT = "";
var KEY_ESC = "27,27";
var KEY_HOME = "63273,63273";
var KEY_END = "63275,63275";
var KEY_PGUP = "63276,63276";
var KEY_PGDN = "63277,63277";
var KEY_BKSPC = "8,8";
var KEY_SPC = "32,32";
var KEY_ENTER = "3,3";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,9";
var KEY_Q = "113,113";
var KEY_W = "119,119";
var KEY_E = "101,101";
var KEY_R = "114,114";
var KEY_T = "116,116";
var KEY_Y = "121,121";
var KEY_U = "117,117";
var KEY_I = "105,105";
var KEY_O = "111,111";
var KEY_P = "112,112";
var KEY_QQ = "81,81!";
var KEY_WW = "87,87!";
var KEY_EE = "69,69!";
var KEY_RR = "82,82!";
var KEY_TT = "84,84!";
var KEY_YY = "89,89!";
var KEY_UU = "85,85!";
var KEY_II = "73,73!";
var KEY_OO = "79,79!";
var KEY_PP = "80,80!";
var KEY_A = "97,97";
var KEY_S = "115,115";
var KEY_D = "100,100";
var KEY_F = "102,102";
var KEY_G = "103,103";
var KEY_H = "104,104";
var KEY_J = "106,106";
var KEY_K = "107,107";
var KEY_L = "108,108";
var KEY_AA = "65,65!";
var KEY_SS = "83,83!";
var KEY_DD = "68,68!";
var KEY_FF = "70,70!";
var KEY_GG = "71,71!";
var KEY_HH = "72,72!";
var KEY_JJ = "74,74!";
var KEY_KK = "75,75!";
var KEY_LL = "76,76!";
var KEY_Z = "122,122";
var KEY_X = "120,120";
var KEY_C = "99,99";
var KEY_V = "118,118";
var KEY_B = "98,98";
var KEY_N = "110,110";
var KEY_M = "109,109";
var KEY_ZZ = "90,90!";
var KEY_XX = "88,88!";
var KEY_CC = "67,67!";
var KEY_VV = "86,86!";
var KEY_BB = "66,66!";
var KEY_NN = "78,78!";
var KEY_MM = "77,77!";
var KEY_1 = "49,49";
var KEY_2 = "50,50";
var KEY_3 = "51,51";
var KEY_4 = "52,52";
var KEY_5 = "53,53";
var KEY_6 = "54,54";
var KEY_7 = "55,55";
var KEY_8 = "56,56";
var KEY_9 = "57,57";
var KEY_0 = "48,48";
var KEY_BANG = "33,33!";
var KEY_AT = "64,64!";
var KEY_HASH = "35,35!";
var KEY_DOLLAR = "36,36!";
var KEY_MOD = "37,37!";
var KEY_CARET = "94,94!";
var KEY_AMP = "38,38!";
var KEY_AST = "42,42!";
var KEY_LPAR = "40,40!";
var KEY_RPAR = "41,41!";
var KEY_MINUS = "45,45";
var KEY_UNDER = "95,95!";
var KEY_PLUS = "43,43!";
var KEY_EQ = "61,61";
var KEY_LBRACE = "123,123!";
var KEY_RBRACE = "125,125!";
var KEY_LBRACK = "91,91";
var KEY_RBRACK = "93,93";
var KEY_PIPE = "124,124!";
var KEY_SLASH = "92,92";
var KEY_COLON = "186,186!";
var KEY_SEMI = "186,186";
var KEY_QUOTE = "34,34!";
var KEY_APOS = "39,39";
var KEY_BSLASH = "47,47";
var KEY_QUEST = "63,63!";
var KEY_COMMA = "44,44";
var KEY_DOT = "46,46";
var KEY_TILDE = "126,126!";
var KEY_TICK = "96,96";
var KEY_LT = "60,60!";
var KEY_GT = "62,62!";
var KEY_LEFT = "37,37";
var KEY_UP = "38,38";
var KEY_RIGHT = "39,39";
var KEY_DOWN = "40,40";
    """

def keyboard_saf_win():
    return """
var KEY_SHIFT = "16,16!";
var KEY_CTRL = "17,17";
var KEY_ALT = "18,18";
var KEY_ESC = "27,27";
var KEY_HOME = "36,36";
var KEY_END = "35,35";
var KEY_PGUP = "33,33";
var KEY_PGDN = "34,34";
var KEY_BKSPC = "8,8";
var KEY_SPC = "32,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,9";
var KEY_Q = "113,113";
var KEY_W = "119,119";
var KEY_E = "101,101";
var KEY_R = "114,114";
var KEY_T = "116,116";
var KEY_Y = "121,121";
var KEY_U = "117,117";
var KEY_I = "105,105";
var KEY_O = "111,111";
var KEY_P = "112,112";
var KEY_QQ = "81,81!";
var KEY_WW = "87,87!";
var KEY_EE = "69,69!";
var KEY_RR = "82,82!";
var KEY_TT = "84,84!";
var KEY_YY = "89,89!";
var KEY_UU = "85,85!";
var KEY_II = "73,73!";
var KEY_OO = "79,79!";
var KEY_PP = "80,80!";
var KEY_A = "97,97";
var KEY_S = "115,115";
var KEY_D = "100,100";
var KEY_F = "102,102";
var KEY_G = "103,103";
var KEY_H = "104,104";
var KEY_J = "106,106";
var KEY_K = "107,107";
var KEY_L = "108,108";
var KEY_AA = "65,65!";
var KEY_SS = "83,83!";
var KEY_DD = "68,68!";
var KEY_DD = "68,68!";
var KEY_GG = "71,71!";
var KEY_HH = "72,72!";
var KEY_JJ = "74,74!";
var KEY_KK = "75,75!";
var KEY_LL = "76,76!";
var KEY_Z = "122,122";
var KEY_X = "120,120";
var KEY_C = "99,99";
var KEY_V = "118,118";
var KEY_B = "98,98";
var KEY_N = "110,110";
var KEY_M = "109,109";
var KEY_ZZ = "90,90!";
var KEY_XX = "88,88!";
var KEY_CC = "67,67!";
var KEY_VV = "86,86!";
var KEY_BB = "66,66!";
var KEY_NN = "78,78!";
var KEY_MM = "77,77!";
var KEY_1 = "49,49";
var KEY_2 = "50,50";
var KEY_3 = "51,51";
var KEY_4 = "52,52";
var KEY_5 = "53,53";
var KEY_6 = "54,54";
var KEY_7 = "55,55";
var KEY_8 = "56,56";
var KEY_9 = "57,57";
var KEY_0 = "48,48";
var KEY_BANG = "33,33!";
var KEY_AT = "64,64!";
var KEY_HASH = "35,35!";
var KEY_DOLLAR = "36,36!";
var KEY_MOD = "37,37!";
var KEY_CARET = "94,94!";
var KEY_AMP = "38,38!";
var KEY_AST = "42,42!";
var KEY_LPAR = "40,40!";
var KEY_RPAR = "41,41!";
var KEY_MINUS = "45,45";
var KEY_UNDER = "95,95!";
var KEY_PLUS = "43,43!";
var KEY_EQ = "61,61";
var KEY_LBRACE = "123,123!";
var KEY_RBRACE = "125,125!";
var KEY_LBRACK = "91,91";
var KEY_RBRACK = "93,93";
var KEY_PIPE = "124,124!";
var KEY_SLASH = "92,92";
var KEY_COLON = "58,58!";
var KEY_SEMI = "59,59";
var KEY_QUOTE = "34,34!";
var KEY_APOS = "39,39";
var KEY_BSLASH = "47,47";
var KEY_QUEST = "63,63!";
var KEY_COMMA = "44,44";
var KEY_DOT = "46,46";
var KEY_TILDE = "126,126!";
var KEY_TICK = "96,96";
var KEY_LT = "60,60!";
var KEY_GT = "62,62!";
var KEY_LEFT = "37,37";
var KEY_UP = "38,38";
var KEY_RIGHT = "39,39";
var KEY_DOWN = "40,40";
"""

# These are the same as of 12 August 2009.
def keyboard_chr_win():
    return keyboard_saf_win()

def keyboard_chr_lin():
    return """
var KEY_SHIFT = "16,16";
var KEY_CTRL = "17,17";
var KEY_ALT = "18,18";
var KEY_ESC = "27,27";
var KEY_HOME = "36,36";
var KEY_END = "35,35";
var KEY_PGUP = "33,33";
var KEY_PGDN = "34,34";
var KEY_BKSPC = "8,8";
var KEY_SPC = "32,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,9";
var KEY_Q = "113,113";
var KEY_W = "119,119";
var KEY_E = "101,101";
var KEY_R = "114,114";
var KEY_T = "116,116";
var KEY_Y = "121,121";
var KEY_U = "117,117";
var KEY_I = "105,105";
var KEY_O = "111,111";
var KEY_P = "112,112";
var KEY_QQ = "81,81!";
var KEY_WW = "87,87!";
var KEY_EE = "69,69!";
var KEY_RR = "82,82!";
var KEY_TT = "84,84!";
var KEY_YY = "89,89!";
var KEY_UU = "85,85!";
var KEY_II = "73,73!";
var KEY_OO = "79,79!";
var KEY_PP = "80,80!";
var KEY_A = "97,97";
var KEY_S = "115,115";
var KEY_D = "100,100";
var KEY_F = "102,102";
var KEY_G = "103,103";
var KEY_H = "104,104";
var KEY_J = "106,106";
var KEY_K = "107,107";
var KEY_L = "108,108";
var KEY_AA = "65,65!";
var KEY_SS = "83,83!";
var KEY_DD = "68,68!";
var KEY_DD = "68,68!";
var KEY_GG = "71,71!";
var KEY_HH = "72,72!";
var KEY_JJ = "74,74!";
var KEY_KK = "75,75!";
var KEY_LL = "76,76!";
var KEY_Z = "122,122";
var KEY_X = "120,120";
var KEY_C = "99,99";
var KEY_V = "118,118";
var KEY_B = "98,98";
var KEY_N = "110,110";
var KEY_M = "109,109";
var KEY_ZZ = "90,90!";
var KEY_XX = "88,88!";
var KEY_CC = "67,67!";
var KEY_VV = "86,86!";
var KEY_BB = "66,66!";
var KEY_NN = "78,78!";
var KEY_MM = "77,77!";
var KEY_1 = "49,49";
var KEY_2 = "50,50";
var KEY_3 = "51,51";
var KEY_4 = "52,52";
var KEY_5 = "53,53";
var KEY_6 = "54,54";
var KEY_7 = "55,55";
var KEY_8 = "56,56";
var KEY_9 = "57,57";
var KEY_0 = "48,48";
var KEY_BANG = "33,33!";
var KEY_AT = "64,64!";
var KEY_HASH = "35,35!";
var KEY_DOLLAR = "36,36!";
var KEY_MOD = "37,37!";
var KEY_CARET = "94,94!";
var KEY_AMP = "38,38!";
var KEY_AST = "42,42!";
var KEY_LPAR = "40,40!";
var KEY_RPAR = "41,41!";
var KEY_MINUS = "45,45";
var KEY_UNDER = "95,95!";
var KEY_PLUS = "43,43!";
var KEY_EQ = "61,61";
var KEY_LBRACE = "123,123!";
var KEY_RBRACE = "125,125!";
var KEY_LBRACK = "91,91";
var KEY_RBRACK = "93,93";
var KEY_PIPE = "124,124!";
var KEY_SLASH = "92,92";
var KEY_COLON = "58,58!";
var KEY_SEMI = "59,59";
var KEY_QUOTE = "34,34!";
var KEY_APOS = "39,39";
var KEY_BSLASH = "47,47";
var KEY_QUEST = "63,63!";
var KEY_COMMA = "44,44";
var KEY_DOT = "46,46";
var KEY_TILDE = "126,126!";
var KEY_TICK = "96,96";
var KEY_LT = "60,60!";
var KEY_GT = "62,62!";
var KEY_LEFT = "37,37";
var KEY_UP = "38,38";
var KEY_RIGHT = "39,39";
var KEY_DOWN = "40,40";
"""

def keyboard_konq():
    return """
var KEY_SHIFT = "16,16";
var KEY_CTRL = "20,20";
var KEY_ALT = "18,18";
var KEY_ESC = "27,27";
var KEY_HOME = "36,36";
var KEY_END = "35,35";
var KEY_PGUP = "33,33";
var KEY_PGDN = "34,34";
var KEY_BKSPC = "8,8";
var KEY_SPC = "32,32";
var KEY_ENTER = "13,13";
var KEY_RETURN = "13,13";
var KEY_TAB = "9,9";
var KEY_Q = "113,113";
var KEY_W = "119,119";
var KEY_E = "101,101";
var KEY_R = "114,114";
var KEY_T = "116,116";
var KEY_Y = "121,121";
var KEY_U = "117,117";
var KEY_I = "105,105";
var KEY_O = "111,111";
var KEY_P = "112,112";
var KEY_QQ = "81,81!";
var KEY_WW = "87,87!";
var KEY_EE = "69,69!";
var KEY_RR = "82,82!";
var KEY_TT = "84,84!";
var KEY_YY = "89,89!";
var KEY_UU = "85,85!";
var KEY_II = "73,73!";
var KEY_OO = "79,79!";
var KEY_PP = "80,80!";
var KEY_A = "97,97";
var KEY_S = "115,115";
var KEY_D = "100,100";
var KEY_F = "102,102";
var KEY_G = "103,103";
var KEY_H = "104,104";
var KEY_J = "106,106";
var KEY_K = "107,107";
var KEY_L = "108,108";
var KEY_AA = "65,65!";
var KEY_SS = "83,83!";
var KEY_DD = "68,68!";
var KEY_FF = "70,70!";
var KEY_GG = "71,71!";
var KEY_HH = "72,72!";
var KEY_JJ = "74,74!";
var KEY_KK = "75,75!";
var KEY_LL = "76,76!";
var KEY_Z = "122,122";
var KEY_X = "120,120";
var KEY_C = "99,99";
var KEY_V = "118,118";
var KEY_B = "98,98";
var KEY_N = "110,110";
var KEY_M = "109,109";
var KEY_ZZ = "90,90!";
var KEY_XX = "88,88!";
var KEY_CC = "67,67!";
var KEY_VV = "86,86!";
var KEY_BB = "66,66!";
var KEY_NN = "78,78!";
var KEY_MM = "77,77!";
var KEY_1 = "49,49";
var KEY_2 = "50,50";
var KEY_3 = "51,51";
var KEY_4 = "52,52";
var KEY_5 = "53,53";
var KEY_6 = "54,54";
var KEY_7 = "55,55";
var KEY_8 = "56,56";
var KEY_9 = "57,57";
var KEY_0 = "48,48";
var KEY_BANG = "33,33!";
var KEY_AT = "64,64!";
var KEY_HASH = "35,35!";
var KEY_DOLLAR = "36,36!";
var KEY_MOD = "37,37!";
var KEY_CARET = "94,94!";
var KEY_AMP = "38,38!";
var KEY_AST = "42,42!";
var KEY_LPAR = "40,40!";
var KEY_RPAR = "41,41!";
var KEY_MINUS = "45,45";
var KEY_UNDER = "95,95!";
var KEY_PLUS = "43,43!";
var KEY_EQ = "61,61";
var KEY_LBRACE = "123,123!";
var KEY_RBRACE = "125,125!";
var KEY_LBRACK = "91,91";
var KEY_RBRACK = "93,93";
var KEY_PIPE = "124,124!";
var KEY_SLASH = "92,92";
var KEY_COLON = "58,58!";
var KEY_SEMI = "59,59";
var KEY_QUOTE = "34,34!";
var KEY_APOS = "39,39";
var KEY_BSLASH = "47,47";
var KEY_QUEST = "63,63!";
var KEY_COMMA = "44,44";
var KEY_DOT = "46,46";
var KEY_TILDE = "126,126!";
var KEY_TICK = "96,96";
var KEY_LT = "60,60!";
var KEY_GT = "62,62!";
var KEY_LEFT = "37,37";
var KEY_UP = "38,38";
var KEY_RIGHT = "39,39";
var KEY_DOWN = "40,40";
    """

def keyboard_ie():
    return """
var KEY_SHIFT = "16,undefined!";
var KEY_CTRL = "20,undefined";
var KEY_ALT = "18,undefined";
var KEY_ESC = "27,undefined";
var KEY_HOME = "36,undefined";
var KEY_END = "35,undefined";
var KEY_PGUP = "33,undefined";
var KEY_PGDN = "34,undefined";
var KEY_BKSPC = "8,undefined";
var KEY_SPC = "32,undefined";
var KEY_ENTER = "13,undefined";
var KEY_RETURN = "13,undefined";
var KEY_TAB = "9,undefined";
var KEY_Q = "81,undefined";
var KEY_W = "87,undefined";
var KEY_E = "69,undefined";
var KEY_R = "82,undefined";
var KEY_T = "84,undefined";
var KEY_Y = "89,undefined";
var KEY_U = "85,undefined";
var KEY_I = "73,undefined";
var KEY_O = "79,undefined";
var KEY_P = "80,undefined";
var KEY_QQ = "81,undefined!";
var KEY_WW = "87,undefined!";
var KEY_EE = "69,undefined!";
var KEY_RR = "82,undefined!";
var KEY_TT = "84,undefined!";
var KEY_YY = "89,undefined!";
var KEY_UU = "85,undefined!";
var KEY_II = "73,undefined!";
var KEY_OO = "79,undefined!";
var KEY_PP = "80,undefined!";
var KEY_A = "65,undefined";
var KEY_S = "83,undefined";
var KEY_D = "68,undefined";
var KEY_F = "70,undefined";
var KEY_G = "71,undefined";
var KEY_H = "72,undefined";
var KEY_J = "74,undefined";
var KEY_K = "75,undefined";
var KEY_L = "76,undefined";
var KEY_AA = "65,undefined!";
var KEY_SS = "83,undefined!";
var KEY_DD = "68,undefined!";
var KEY_FF = "70,undefined!";
var KEY_GG = "71,undefined!";
var KEY_HH = "72,undefined!";
var KEY_JJ = "74,undefined!";
var KEY_KK = "75,undefined!";
var KEY_LL = "76,undefined!";
var KEY_Z = "90,undefined";
var KEY_X = "88,undefined";
var KEY_C = "67,undefined";
var KEY_V = "86,undefined";
var KEY_B = "66,undefined";
var KEY_N = "78,undefined";
var KEY_M = "77,undefined";
var KEY_ZZ = "90,undefined!";
var KEY_XX = "88,undefined!";
var KEY_CC = "67,undefined!";
var KEY_VV = "86,undefined!";
var KEY_BB = "66,undefined!";
var KEY_NN = "78,undefined!";
var KEY_MM = "77,undefined!";
var KEY_1 = "49,undefined";
var KEY_2 = "50,undefined";
var KEY_3 = "51,undefined";
var KEY_4 = "52,undefined";
var KEY_5 = "53,undefined";
var KEY_6 = "54,undefined";
var KEY_7 = "55,undefined";
var KEY_8 = "56,undefined";
var KEY_9 = "57,undefined";
var KEY_0 = "48,undefined";
var KEY_BANG = "49,undefined!";
var KEY_AT = "50,undefined!";
var KEY_HASH = "51,undefined!";
var KEY_DOLLAR = "52,undefined!";
var KEY_MOD = "53,undefined!";
var KEY_CARET = "54,undefined!";
var KEY_AMP = "55,undefined!";
var KEY_AST = "56,undefined!";
var KEY_LPAR = "57,undefined!";
var KEY_RPAR = "48,undefined!";
var KEY_MINUS = "189,undefined";
var KEY_UNDER = "189,undefined!";
var KEY_PLUS = "187,undefined!";
var KEY_EQ = "187,undefined";
var KEY_LBRACE = "219,undefined!";
var KEY_RBRACE = "221,undefined!";
var KEY_LBRACK = "219,undefined";
var KEY_RBRACK = "221,undefined";
var KEY_PIPE = "220,undefined!";
var KEY_SLASH = "220,undefined";
var KEY_COLON = "186,undefined!";
var KEY_SEMI = "186,undefined";
var KEY_QUOTE = "222,undefined!";
var KEY_APOS = "222,undefined";
var KEY_BSLASH = "191,undefined";
var KEY_QUEST = "191,undefined!";
var KEY_COMMA = "188,undefined";
var KEY_DOT = "190,undefined";
var KEY_TILDE = "192,undefined!";
var KEY_TICK = "192,undefined";
var KEY_LT = "188,undefined!";
var KEY_GT = "190,undefined!";
var KEY_LEFT = "37,undefined";
var KEY_UP = "38,undefined";
var KEY_RIGHT = "39,undefined";
var KEY_DOWN = "40,undefined";
    """

# Define mapping from 2-letter OS/Browser codes to the
# functions defined above.

# Note: The notebook identifies Chrome on Windows and Chromium on
# Linux as Safari, so we use 's' instead of 'c'.
keyboard_map = {'mw':keyboard_moz_win,
                'ml':keyboard_moz_lin,
                'mm':keyboard_moz_mac,
                'ow':keyboard_op_win,
                'ol':keyboard_op_lin,
                'om':keyboard_op_mac,
                'sw':keyboard_saf_win,
                'sm':keyboard_saf_mac,
                'sl':keyboard_chr_lin,
                'kl':keyboard_konq,
                'iw':keyboard_ie}
