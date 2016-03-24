gulp = require "gulp"
gutil = require "gulp-util"
ts = require 'gulp-typescript'
run = require 'run-sequence'

reporter = ts.reporter.nullReporter()

compile = (name) ->
  project = ts.createProject("./examples/#{name}/tsconfig.json")
  project.src()
         .pipe(ts(project, {}, reporter).on('error', (err) -> gutil.log(err.message)))
         .js
         .pipe(gulp.dest("./"))

gulp.task "examples:anscombe", ["scripts:build", "styles:build"], () -> compile("anscombe")
gulp.task "examples:burtin",   ["scripts:build", "styles:build"], () -> compile("burtin")
gulp.task "examples:tap",      ["scripts:build", "styles:build"], () -> compile("tap")
gulp.task "examples:stocks",   ["scripts:build", "styles:build"], () -> compile("stocks")

gulp.task "examples", (cb) -> run(["examples:anscombe", 
                                   "examples:burtin",
                                   "examples:tap",
                                   "examples:stocks"],
                                   cb)
