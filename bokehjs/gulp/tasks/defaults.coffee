_ = require "underscore"
fs = require "fs"
path = require "path"
mkdirp = require "mkdirp"
child_process = require "child_process"
gulp = require "gulp"
gutil = require "gulp-util"
argv = require("yargs").argv
paths = require "../paths"

gulp.task "defaults:generate", (cb) ->
  if argv.verbose then gutil.log("Generating defaults.json")
  bokehjsdir = path.normalize(process.cwd())
  basedir = path.normalize(bokehjsdir + "/..")
  oldpath = process.env['PYTHONPATH']
  if oldpath?
    pypath = "#{basedir}:#{oldpath}"
  else
    pypath = basedir
  env = _.extend({}, process.env, { PYTHONPATH: pypath })
  proc = child_process.spawn("python", ['./gulp/tasks/generate_defaults.py'], {
    env: env,
    cwd: bokehjsdir
  })
  json = ""
  proc.stdout.on 'data', (data) -> json += data
  proc.stderr.on 'data', (data) -> gutil.log("generate_defaults.py: #{data}")
  proc.on 'close', (code) ->
    if code != 0
      cb(new Error("generate_defaults.py exited code #{code}"))
    else
      defaultsDir = paths.buildDir.all
      mkdirp defaultsDir, (err) ->
        if err
          cb(err)
        else
          fs.writeFile(path.join(defaultsDir, "defaults.json"), json, cb)

  null # XXX: this is extremely important to allow cb() to work
