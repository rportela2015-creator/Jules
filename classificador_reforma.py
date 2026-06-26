import csv
import logging
import os

# Configuração do Log
logging.basicConfig(
    filename='processamento.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Mapeamento de NCMs com Redução de 60% (Baseado no PLP 68/2024 - Materiais Básicos)
# Nota: Esta lista é exemplificativa conforme as discussões e anexos do PLP 68/2024
NCM_REDUCAO_60 = {
    '2505.10.00', # Areia
    '2523.29.10', # Cimento
    '6904.10.00', # Tijolos cerâmicos
    '3214.90.00', # Argamassas
    '2516.90.00', # Brita/Pedrisco
    '3917',       # Tubos e conexões (prefixo)
}

def classificar_ncm(ncm):
    """
    Avalia o NCM e retorna o enquadramento tributário conforme PLP 68/2024.
    """
    ncm_clean = ncm.strip()

    # Verifica correspondência exata ou por prefixo (para categorias como plásticos/tubos)
    if ncm_clean in NCM_REDUCAO_60:
        return 'Redução de 60%'

    for prefix in NCM_REDUCAO_60:
        if ncm_clean.startswith(prefix) and len(prefix) >= 4:
            return 'Redução de 60%'

    return 'Alíquota de Referência Padrão'

def processar_materiais(input_file, output_file):
    try:
        if not os.path.exists(input_file):
            logging.error(f"Arquivo de entrada não encontrado: {input_file}")
            return

        with open(input_file, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames + ['Enquadramento_Tributario']

            rows = list(reader)
            total_lidos = len(rows)
            classificados_reducao = 0
            classificados_padrao = 0

            output_rows = []
            for row in rows:
                enquadramento = classificar_ncm(row['ncm'])
                row['Enquadramento_Tributario'] = enquadramento
                output_rows.append(row)

                if enquadramento == 'Redução de 60%':
                    classificados_reducao += 1
                else:
                    classificados_padrao += 1

        with open(output_file, mode='w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)

        logging.info("Processamento concluído com sucesso.")
        logging.info(f"Total de itens lidos: {total_lidos}")
        logging.info(f"Itens com Redução de 60%: {classificados_reducao}")
        logging.info(f"Itens com Alíquota Padrão: {classificados_padrao}")

        print(f"Sucesso! {total_lidos} itens processados.")
        print(f"Verifique o log 'processamento.log' para detalhes.")

    except Exception as e:
        logging.error(f"Erro durante o processamento: {str(e)}")
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    input_csv = 'ncm_materiais.csv'
    output_csv = 'ncm_materiais_classificados.csv'
    processar_materiais(input_csv, output_csv)
