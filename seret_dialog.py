"""
getting requested days list snf minimum movie rate using tkinter dialog box.
"""
import tkinter
import datetime
import sys


def get_day_rate():
    """ 
    getting requested days list snf minimum movie rate using tkinter dialog box.
    Args:

    Returns:
        days_requested (list)
        grade_min (float)
    """
    def exit_ok():
        master.destroy()

    def exit_quit():
        master.destroy()
        sys.exit()

    day_name = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']
    master = tkinter.Tk()
    check_var = [tkinter.BooleanVar(value=False),
                 tkinter.BooleanVar(value=False),
                 tkinter.BooleanVar(value=False),
                 tkinter.BooleanVar(value=False),
                 tkinter.BooleanVar(value=False),
                 tkinter.BooleanVar(value=False),
                 tkinter.BooleanVar(value=False)]
    # select current weekday as default value. Note:need to adjust because weekday(Monday) = 0
    check_var[(datetime.datetime.today().weekday()+1) % 7].set(True)
    tkinter.Label(master, text=":ימים בחר").grid(row=0, column=4, sticky=tkinter.E)
    for i in range(len(day_name)):
        tkinter.Label(master, text=day_name[i]).grid(row=1+i, column=3,
                                                     sticky=tkinter.E)
        tkinter.Checkbutton(master, offvalue=False, onvalue=True,
                            anchor=tkinter.E,
                            variable=check_var[i]).grid(row=1+i, column=4,
                                                        sticky=tkinter.E,
                                                        padx=(10, 10))
    grade = tkinter.StringVar()
    grade.set(7.5)
    tkinter.Label(master, text=":גולשים מדד").grid(row=0, column=1,
                                                   sticky=tkinter.E)
    tkinter.Entry(master, textvariable=grade,
                  width=3).grid(row=0, column=0, sticky=tkinter.E)
    tkinter.Button(master, text='בטל',
                   command=exit_quit).grid(row=1+len(day_name),
                                           column=0, sticky=tkinter.W, pady=4)
    tkinter.Button(master, text='אשר',
                   command=exit_ok).grid(row=1+len(day_name), column=1,
                                         sticky=tkinter.W, pady=4)
    master.mainloop()
    days_requested = [day.get() for day in check_var]
    grade_min = float(grade.get())
    return days_requested, grade_min

if __name__ == '__main__':
    print(get_day_rate())
