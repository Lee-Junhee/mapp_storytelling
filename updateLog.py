import datetime

print("Please enter your name:")
print("Format: firstnameL")
name = input()

print("\n")
print("Please enter your update:")
update = input()

timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

devlogFile = open("devlog.txt", "a")

devlogFile.write("\n" + name + " -- " + timestamp + "\n")
devlogFile.write(update+"\n\n")

devlogFile.close()
