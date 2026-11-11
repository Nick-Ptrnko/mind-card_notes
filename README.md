Правило у .gitignore ігнорує лише ті файли, які є новими (untracked) і ніколи раніше не додавалися до сховища.
```
git rm --cached mind_card_backup.json
```
У терміналі має з'явитися повідомлення rm 'mind_card_backup.json', що підтверджує вилучення файлу з індексу Git.
```
git add .gitignore
git status
```
