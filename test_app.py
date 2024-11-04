from shiny import App, render, ui
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# chords list for single select element
chords_list = ["None", "I", "i", "II", 'ii', "III", 'iii', "IV", "iv", "V", "v", "VI", "vi", "VII", "vii",
               "I#", "i#", "II#", 'ii#', "III#", 'iii#', "IV#", "iv#", "V#", "v#", "VI#", "vi#", "VII#", "vii#",]


# function to run a query as a single connection
def run_query(query: str, placeholders: list[str]) -> pd.DataFrame:
    connection = sqlite3.connect("db/songs_database.db")
    cur = connection.cursor()
    cur.execute("PRAGMA case_sensitive_like = TRUE;")
    cur.execute(query, placeholders)
    df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
    connection.close()

    return df


app_ui = ui.page_auto(
    ui.input_dark_mode(id="idm"), #Dark mode button
    ui.h2("Chord progression songs finder", style="text-align: center;"), # Header
    ui.layout_column_wrap( # all singe select elements
        ui.input_select(  
            "chord1",  
            "First chord",  
            chords_list,  
        ),
            ui.input_select(  
            "chord2",  
            "Second chord",  
            chords_list,  
        ),
            ui.input_select(  
            "chord3",  
            "Third chord",  
            chords_list,  
        ),
            ui.input_select(  
            "chord4",  
            "Fourth chord",  
            chords_list,  
        ),
        gap="2rem",
    ),
    ui.output_text("songs_count"), # text field for songs count
    ui.layout_columns( # table and graph
        ui.output_data_frame("songs"),
        ui.output_plot("chord_plot", width="650px", height="550px", click=True),
        gap="2rem",
    ),
)


def server(input, output, session):

    @render.data_frame
    def songs():
        chords = [input.chord1(), input.chord2(), input.chord3(), input.chord4()]

        chords_filter = [
            '%-' + '-'.join(val for val in chords if val != 'None') + '-%',
            '-'.join(val for val in chords if val != 'None') + '-%',
            '%-' + '-'.join(val for val in chords if val != 'None'),
            '-'.join(val for val in chords if val != 'None')
        ]

        # getting 10 songs with particular progression
        df = run_query('''
            select name, artist, section, progression from songSectionDataClean 
            where 
                trim(progression) like ? or 
                trim(progression) like ? or 
                trim(progression) like ? or
                trim(progression) = ?
            limit 20;
        ''', chords_filter)

        return render.DataTable(df)

    @render.text
    def songs_count():
        chords = [input.chord1(), input.chord2(), input.chord3(), input.chord4()]

        chords_filter = [
            '%-' + '-'.join(val for val in chords if val != 'None') + '-%',
            '-'.join(val for val in chords if val != 'None') + '-%',
            '%-' + '-'.join(val for val in chords if val != 'None'),
            '-'.join(val for val in chords if val != 'None')
        ]

        # getting count of songs with particular progression
        df = run_query('''
            select count(*) from songSectionDataClean 
            where 
                trim(progression) like ? or 
                trim(progression) like ? or 
                trim(progression) like ? or
                trim(progression) = ?
            limit 10;
        ''', chords_filter)

        return 'Pieces with this progression: ' + str(df.iat[0, 0])

    @render.plot
    def chord_plot():
        chords = [input.chord1(), input.chord2(), input.chord3(), input.chord4()]
        curr_chords = '-'.join(val for val in chords if val != 'None')

        # getting count of next chords
        df = run_query(f'''
            WITH next_chords AS (
            SELECT 
                TRIM(SUBSTR(progression, 
                    INSTR(progression, '{curr_chords}') + LENGTH('{curr_chords}') + 1, 
                    CASE 
                        WHEN INSTR(SUBSTR(progression, INSTR(progression, '{curr_chords}') + LENGTH('{curr_chords}') + 1), '-') > 0 THEN 
                            INSTR(SUBSTR(progression, INSTR(progression, '{curr_chords}') + LENGTH('{curr_chords}') + 1), '-') - 1
                        ELSE 
                            LENGTH(SUBSTR(progression, INSTR(progression, '{curr_chords}') + LENGTH('{curr_chords}') + 1))
                    END
                )) AS next_chord
            FROM 
                songSectionDataClean
            WHERE 
                progression LIKE '%{curr_chords}-%'
            )
            SELECT 
                next_chord, 
                COUNT(*) AS count
            FROM 
                next_chords
            WHERE 
                next_chord != '' and next_chord not like '%-%' and next_chord not like '%#%' and next_chord not like '%b%'
            GROUP BY 
                next_chord
            ORDER BY 
                count DESC;
        ''', [])
        
        if df.empty:
            return

        df_pivot = df.pivot_table(index='next_chord', values='count', aggfunc='sum')
        df_sorted = df_pivot.sort_values(by='count', ascending=False)

        fig, ax = plt.subplots(figsize=(6.5, 5.5))

        heatmap = sns.heatmap(df_sorted, annot=True, fmt=".2f", cmap="magma", 
                            annot_kws={"size": 12}, 
                            cbar=False,
                            xticklabels=False,
                            yticklabels=True)

        # recolor the chart depending on the background mode
        if input.idm() == 'light':
            plt.title('Next Chord Heatmap', fontsize=18, fontweight='bold', color="black")
            plt.xlabel('Count', fontsize=14, color="black")
            plt.ylabel('Next Chord', fontsize=14, color="black")

            ax.tick_params(axis='x', labelsize=12)
            ax.tick_params(axis='y', labelsize=12)

            for tick in ax.get_xticklabels():
                tick.set_color("black")
            for tick in ax.get_yticklabels():
                tick.set_color("black")

            fig.patch.set_facecolor('#FFFFFF')
            ax.set_facecolor('#FFFFFF')
        else:
            plt.title('Next Chord Heatmap', fontsize=18, fontweight='bold', color="white")
            plt.xlabel('Count', fontsize=14, color="white")
            plt.ylabel('Next Chord', fontsize=14, color="white")

            ax.tick_params(axis='x', labelsize=12, color="white")
            ax.tick_params(axis='y', labelsize=12, color="white")

            for tick in ax.get_xticklabels():
                tick.set_color("white")
            for tick in ax.get_yticklabels():
                tick.set_color("white")

            fig.patch.set_facecolor('#1d1f21')
            ax.set_facecolor('#1d1f21')

        return fig


app = App(app_ui, server)
