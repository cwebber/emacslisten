;;; emacslisten.el --- control emacs with your voice!

;; Copyright 2013 Christopher Allan Webber

;; Emacslisten is free software; you can redistribute it and/or modify it
;; under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 3, or (at your option)
;; any later version.
;;
;; Emacslisten is distributed in the hope that it will be useful, but WITHOUT
;; ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
;; or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
;; License for more details.
;;
;; You should have received a copy of the GNU General Public License
;; along with Emacslisten.  If not, see <http://www.gnu.org/licenses/>.

;; This doesn't do anything yet.  I sure hope it will, though :)


(defun emacslisten-handle-partial-result (hyp uttid)
  (message "Partial: %s" hyp))

(defun emacslisten-handle-final-result (hyp uttid)
  (message "Result: %s" hyp))

(defun emacslisten-connect-to-daemon ()
  (interactive)
  (dbus-register-signal
   :session
   "org.dustycloud.EmacsListen" "/org/dustycloud/EmacsListen/daemon"
   "org.dustycloud.EmacsListen" "final_result"
   'emacslisten-handle-final-result)
  (dbus-register-signal
   :session
   "org.dustycloud.EmacsListen" "/org/dustycloud/EmacsListen/daemon"
   "org.dustycloud.EmacsListen" "partial_result"
   'emacslisten-handle-partial-result))
  
