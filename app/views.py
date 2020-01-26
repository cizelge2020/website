from django.shortcuts import render
import pulp
import numpy as np
import pandas as pd

def home(request):

    return render(request,'home.html')


def form(request):
    # Datanın okunması
    data = pd.read_excel('Data/data_V2.xlsx', index_col=0)
    data.reset_index(drop=True, inplace=True)

    # Personel İsimlerinin ve Bölüm isimlerinin Form'da gösterilmesi için çekilmesi
    name_list = zip(data['Personel Ad Soyad'].index, data['Personel Ad Soyad'].values)
    division_list = zip(data.drop('Personel Ad Soyad', axis=1).T.reset_index()['index'].index,
                        data.drop('Personel Ad Soyad', axis=1).T.reset_index()['index'].values)

    return render(request, 'form.html', context={'name_list': name_list, 'division_list': division_list})


def schedule(request):
    # Form'da seçilen personel ve bölümlerin çekilmesi
    staffs_string_list = request.GET.getlist('staff')
    divisions_string_list = request.GET.getlist('division')

    # Çekilen listelerin string formatından integer formatına dönüştürülmesi
    selected_staffs = []
    selected_divisions = []
    for i in staffs_string_list:
        selected_staffs.append(int(i))
    for i in divisions_string_list:
        selected_divisions.append(int(i))

    # Datanın okunması
    data = pd.read_excel('Data/data_V2.xlsx', index_col=0)
    data.reset_index(drop=True, inplace=True)

    # Personel ve  Bölüm isimlerinin Filtereleme için Datadan alınması
    staff_dict = dict(zip(data['Personel Ad Soyad'].index, data['Personel Ad Soyad'].values))
    division_dict = dict(zip(data.drop('Personel Ad Soyad', axis=1).T.reset_index()['index'].index,
                             data.drop('Personel Ad Soyad', axis=1).T.reset_index()['index'].values))

    # Optimizasyonda kullanılacak olan kişi ve bölüm isimlerinin alınması
    staff_opt_list = [staff_dict[i] for i in selected_staffs]
    division_opt_list = [division_dict[i] for i in selected_divisions]

    # Seçilen Kişi ve Bölümlere göre Datanın filtrelenmesi
    names = data[data['Personel Ad Soyad'].isin(staff_opt_list)]['Personel Ad Soyad']
    data = data[data['Personel Ad Soyad'].isin(staff_opt_list)].filter(items=division_opt_list, axis=1)
    data['Personel Ad Soyad'] = names

    # Kişi, Bölüm ve Performans bilgilenin, Opt için tutulması
    staff = dict(zip(data['Personel Ad Soyad'].reset_index().index, data['Personel Ad Soyad'].values))
    division = dict(zip(data.drop('Personel Ad Soyad', axis=1).T.reset_index()['index'].index,
                        data.drop('Personel Ad Soyad', axis=1).T.reset_index()['index'].values))
    performance = np.array(data.drop('Personel Ad Soyad', axis=1).values).astype(int)

    # OPTİMİZASYON PROBLEMİNİN TANIMLANMASI
    problem = pulp.LpProblem('Staff_Assigment_Problem', pulp.LpMaximize)

    # DEĞİŞKENLERİN TANIMLANMASI
    X_assign = pulp.LpVariable.dicts('Assign', (staff, division), lowBound=0, upBound=1, cat=pulp.LpBinary)

    # AMAÇ FONKSİYONUNUN TANIMLANMASI
    problem += pulp.lpSum([performance[i][j] * X_assign[i][j] for i in staff for j in division])

    # KISITLARIN TANIMLANMASI
    number_of_staff = len(staff.keys())
    number_of_division = len(division.keys())

    # Staff <= Division
    if number_of_staff <= number_of_division:
        # Her lokasyonda MAKSIMUM 1 kişi olsun.
        for j in division:
            problem += pulp.lpSum([X_assign[i][j] for i in staff]) <= 1

        # Her çalışan KESİNLİKLE ve SADECE 1 bölüme atansın.
        for i in staff:
            problem += pulp.lpSum([X_assign[i][j] for j in division]) == 1

    # Staff > Division
    elif number_of_staff > number_of_division:

        # Her lokasyonda MINIMUM 1 kişi olsun.
        for j in division:
            problem += pulp.lpSum([X_assign[i][j] for i in staff]) >= 1

        # Her çalışan KESİNLİKLE ve SADECE 1 bölüme atansın.
        for i in staff:
            problem += pulp.lpSum([X_assign[i][j] for j in division]) == 1

    # PROBLEMİN ÇÖZÜMÜ VE ÇIKTILARI
    problem.solve()

    objective_score = pulp.value(problem.objective)
    problem_status = pulp.LpStatus[problem.status]

    # Eşleştirilen kişi ve bölümlerin listeye atanması (id olarak)
    staff_list = []
    division_list = []
    assignment_list = []
    for v in problem.variables():
        if v.varValue == 1:
            staff_list.append(int(v.name.split('_')[-2]))
            division_list.append(int(v.name.split('_')[-1]))
            assignment_list.append(v.varValue)

    # id listesinin isim ve bölüm listesine çevirilmesi
    division_result_list = [division[i] for i in division_list]
    staff_result_list = [staff[i] for i in staff_list]

    result_list = zip(staff_result_list, division_result_list)


    # Sayfaya gönderilecekler:
    context = {'staffs': selected_staffs,
               'divisions': selected_divisions,
               'objective_score': objective_score,
               'problem_status': problem_status,
               'division_result_list': division_result_list,
               'staff_result_list': staff_result_list,
               'result_list': result_list}

    return render(request, 'schedule.html', context=context)
