project('cancionero',
          version: '0.1.0',
    meson_version: '>= 0.62.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')

python3 = import('python').find_installation('python3')
run_command(python3, '-m', 'pip', 'install', 'requests', check : true)
run_command(python3, '-m', 'pip', 'install', 'bs4', check : true)

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
