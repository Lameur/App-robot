#!/usr/bin/env ruby

 # This script is used to write a conventional commit message following the
 # Conventional Commits v1.0.0 specification. It prompts the user to choose the
 # type, optional scope, breaking change indicator, summary, and detailed
 # description, then constructs a conforming commit message.

 require 'shellwords'  # For properly escaping strings

 # Direct calls to gum
 def run_gum(cmd)
   `gum #{cmd}`.chomp
 end

 # Function to handle staging changes
 def stage_changes
   # Check if there are any unstaged changes
   unstaged = `git status -s -uno`.lines.map(&:chomp)
   return if unstaged.empty?  # Nothing to do if there are no changes

   # Offer options for staging
   options = ["Add all (git add .)", "Select files"]
   choice = run_gum("choose \"#{options.join('" "')}\" --header \"Changes to stage:\"")

   if choice == options[0]  # "Add all"
     system("git add .")
   elsif choice == options[1]  # "Select files"
     files = unstaged.map { |line| line.split[1] }  # Extract file names
     selected = run_gum("choose --no-limit \"#{files.join('" "')}\" --header \"Select files to stage:\"").split
     system("git add #{selected.map { |f| Shellwords.shellescape(f) }.join(' ')}") unless selected.empty?
   end
 end

 # Main logic
 stage_changes

 types = %w[fix feat docs style refactor test chore revert].join(" ")
 type = run_gum("choose #{types} --header \"Commit type:\"")
 scope = run_gum('input --placeholder "scope (optional)"')
 breaking = run_gum('confirm "Is this a breaking change (!) ?"') == "0" ? "!" : ""

 scope = "(#{scope})" unless scope.empty?

 # Build the summary prefix
 prefix = "#{type}#{scope}#{breaking}: "
 summary = run_gum("input --value \"#{prefix}\" --placeholder \"Summary of this change\"")
 description = run_gum('write --placeholder "Details of this change (optional)"')

 # Handle footers (optional)
 footer = ""
 if run_gum('confirm "Add a footer (e.g., BREAKING CHANGE) ?"') == "0"
   footer_type = run_gum('input --placeholder "Footer type (e.g., BREAKING CHANGE, Refs)"')
   footer_value = run_gum('write --placeholder "Footer value"')
   footer = "\n\n#{footer_type}: #{footer_value}"
 end

 # Construct the full commit message
 full_message = "#{summary}#{description.empty? ? '' : "\n\n#{description}"}#{footer}"

 # Confirmation and commit
 if system("gum confirm \"Commit changes?\"")
   system("git commit -m #{Shellwords.shellescape(full_message)}")
 end
