So, what's THE PLAN?

There is no plan, but there is a vague list of things I want.

I want:

* I want a terminal that can mix text, sprites, and graphics primitives
* I want a way to make noise and a way to play music
* I want an editor that is simple and can only edit one file
* I want a version of Python that is simpler. No imports.
* I want a friendly REPL that is not too featureful.
* I want a modal UI that makes sense

Sounds weird, I know, but it's my project and I make the decisions,
at least for now. Let's go into each bit in detail.

# Terminal that can mix text, sprites, and graphics primitives

I want the 80s experience, and this is part of it. You could use text,
you could use graphics. No event loop, no nothing, just draw and it's
there until you clear it up.

I am implementing this by combining:

* Pyte to implement a vt100 / xterm like
* raylib to draw things on screen
* IPC to send graphical commands to the screen outside the terminal flow

The CobraPy API does most emphatically **not** expose any of that.
Rather, it exposes things like:

`print_at(10,10, "Hello World!")` which will print that string there (in characters, not in pixels!)

`circle(100,100,50,red)` which will draw a red circle at 100,100 (pixels!) with a 50 pixel radius, in red.

This will then use IPC to tell raylib to draw whatever. Yes, this is reinventing X, or Wayland. I know.

And why do we have the vt100 support?

For the prompt and for the editor. Yes, **private APIs, baby**. There will
eventually be some support for more complex apps, exposing this in some way,
but not directly.

# A way to make noise and a way to play music

Raylib has this, just define a reasonable API and expose.

# An editor that is simple and can only edit one file

You have no imports so there is no reason to have more than one file.
Who knows, this may go away. In the meantime, it is what it is.
Again: no fancy completion and so on. SIMPLE.

# A version of Python that is simpler, no imports.

Maybe not even classes. Looking into RestrictedPython. I feel that
people get paralized by choice when they are learning to code. I want
them to hold the whole thing in their head at once.

# Friendly REPL that is not too featureful.

The python REPL is not friendly enough. When you type something wrong it shouts at you.

IPython is too friendly. It gives you things and suggestions and talks to you all the time.

I want something that:

* Maybe has syntax coloring
* **Maybe** autocompletes from:
  * keywords
  * builtins
  * the api provided
  * your locals
* Has reasonable editing
* Doesn't let you input invalid syntax.
* Helps you fix your invalid syntax without having to type everything again

I think I can make that work using the basis of ptpython (prompt_toolkit) which is quite awesome.

# A modal UI that makes sense

* One key goes to the editor. Always.
* The editor has the current program. Always.
* One key runs the current program. If it's running it does nothing.
* One key takes you to the REPL. Always.

So: 3 modes, and clear rules to switch between them. When you are on
the editor, the program is not running. When you are in the REPL,
the program is not running.

Is this going to be interesting to anyone else?

Who knows!
Maybe!
