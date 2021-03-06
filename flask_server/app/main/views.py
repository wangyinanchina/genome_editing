import sys

sys.path.append('/Users/yinan/PycharmProjects/')
import genome_editing.design_sgRNA.design as dsr
from genome_editing.score_sgrna.rs2 import compute_rs2_batch
from flask import Flask, render_template, redirect, url_for, send_from_directory
from . import main
from .forms import DesignSingleSgrnaForm, DesignBatchSgrnaForm, \
    ScoreSgrnaForm, DesignScreen
from .. import db
from ..models import SgrnaDesign
from genome_editing.utils.utilities import model_to_df, reverse_complement

JOB_ID = 0


# home
@main.route('/')
def main_page():
    return render_template("main_page.html")


# design sgRNA
@main.route('/design_sgrna/', methods=['GET', 'POST'])
def design_sgrna():
    return design_sgrna_single_mode()


@main.route('/design_sgrna/<job_id>/')
def design_sgrna_download_link(job_id):
    result_dir = '../results'
    file_name = 'design_sgrna_output_' + str(job_id) + '.csv'
    return send_from_directory(result_dir, file_name, as_attachment=True)


@main.route('/design_sgrna_single_mode/', methods=['GET', 'POST'])
def design_sgrna_single_mode():
    global JOB_ID
    form = DesignSingleSgrnaForm()
    if form.validate_on_submit():
        JOB_ID += 1

        input_type = form.input_type.data
        design_inputs = form.design_input.data
        upstream_len = form.upstream_len.data
        downstream_len = form.downstream_len.data
        flank_len = form.flank_len.data
        sgrna_len = form.sgrna_len.data
        pam = form.pam_seq.data
        pam_rc = reverse_complement(pam)
        ref_genome = form.ref_genome.data

        if input_type == 'Gene Symbol':
            gene_symbols = design_inputs.split('\n')
            gene_symbols = [x.strip() for x in gene_symbols]
            assert len(gene_symbols) == 1, "Too many inputs"
            gene_symbol = gene_symbols[0]
            sgrna_design = dsr.Designer(gene_symbol=gene_symbol,
                                        sgrna_upstream=upstream_len,
                                        sgrna_downstream=downstream_len,
                                        flank=flank_len,
                                        sgrna_length=sgrna_len)
            sgrna_design.get_sgrnas(pams=[pam])
            sgrna_designer_out = sgrna_design.output()
        elif input_type == 'Refseq ID':
            refseq_ids = design_inputs.split('\n')
            refseq_ids = [x.strip() for x in refseq_ids]
            assert len(refseq_ids) == 1, "Too many inputs"
            refseq_id = refseq_ids[0]
            sgrna_design = dsr.Designer(refseq_id=refseq_id,
                                        sgrna_upstream=upstream_len,
                                        sgrna_downstream=downstream_len,
                                        flank=flank_len,
                                        sgrna_length=sgrna_len)
            sgrna_design.get_sgrnas(pams=[pam])
            sgrna_designer_out = sgrna_design.output()
        else:
            seq = design_inputs.split('\n')
            assert len(seq) == 1, "Too many inputs"
            seq = seq[0]
            sgrna_design = dsr.SeqDesigner(seq=seq)
            sgrna_design.get_sgrnas(pams=[pam])
            sgrna_designer_out = sgrna_design.output()

        output_path = './results/design_sgrna_output_' + str(JOB_ID) + '.csv'
        sgrna_designer_out.to_csv(output_path, index=None)
        return render_template('design_sgrna_output.html', job_id=JOB_ID)
    else:
        return render_template('design_sgrna_single_mode.html', form=form)


@main.route('/design_sgrna_batch_mode/', methods=['GET', 'POST'])
def design_sgrna_batch_mode():
    global JOB_ID
    form = DesignBatchSgrnaForm()

    if form.validate_on_submit():
        JOB_ID += 1

        input_type = form.input_type.data
        design_inputs = form.design_input.data
        pam = form.pams.data
        pam_rc = reverse_complement(pam)
        ref_genome = form.ref_genome.data

        if input_type == 'Gene Symbol':
            gene_symbols = design_inputs.split('\n')
            gene_symbols = [x.strip() for x in gene_symbols]
            print(gene_symbols)
            query_out = SgrnaDesign.query.filter(
                SgrnaDesign.gene_symbol.in_(gene_symbols)).filter(
                SgrnaDesign.pam_type.in_([pam, pam_rc])
            ).all()
            sgrna_designer_out = model_to_df(query_out)
        else:
            refseq_ids = design_inputs.split('\n')
            refseq_ids = [x.strip() for x in refseq_ids]
            print(refseq_ids)
            query_out = SgrnaDesign.query.filter(
                SgrnaDesign.refseq_id.in_(refseq_ids)).filter(
                SgrnaDesign.pam_type.in_([pam, pam_rc])
            ).all()
            sgrna_designer_out = model_to_df(query_out)

        output_path = './results/design_sgrna_output_' + str(JOB_ID) + '.csv'
        sgrna_designer_out.to_csv(output_path, index=None)
        return render_template('design_sgrna_output.html', job_id=JOB_ID)
    else:
        return render_template('design_sgrna_batch_mode.html', form=form)


@main.route('/design_screen/', methods=['GET', 'POST'])
def design_screen():
    form = DesignScreen()
    return render_template('design_screen.html', form=form)


# rank sgRNA
@main.route('/score_sgrna/', methods=['GET', 'POST'])
def score_sgrna():
    global JOB_ID
    form = ScoreSgrnaForm()

    if form.validate_on_submit():
        JOB_ID += 1
        seqs = [x.strip() for x in form.seqs.data.split('\n')]
        score_sgrna_out = compute_rs2_batch(seqs)
        output_path = './results/score_sgrna_output_' + str(JOB_ID) + '.csv'
        score_sgrna_out.to_csv(output_path, index=None)
        return render_template('score_sgrna_output.html', job_id=JOB_ID)
    else:
        return render_template('score_sgrna_input.html', form=form)


@main.route('/score_sgrna/<job_id>/')
def score_sgrna_download_link(job_id):
    result_dir = '../results'
    file_name = 'score_sgrna_output_' + str(job_id) + '.csv'
    return send_from_directory(result_dir, file_name, as_attachment=True)


# negative controls
@main.route('/negative_controls/')
def negative_controls():
    return render_template('negative_controls.html')


@main.route('/negative_controls/hg19')
def neg_ctrl_hg19():
    result_dir = '../results'
    file_name = 'hg19_negative_controls.csv'
    return send_from_directory(result_dir, file_name, as_attachment=True)


@main.route('/negative_controls/hg38')
def neg_ctrl_hg38():
    result_dir = '../results'
    file_name = 'hg38_negative_controls.csv'
    return send_from_directory(result_dir, file_name, as_attachment=True)


@main.route('/negative_controls/mm10')
def neg_ctrl_mm10():
    result_dir = '../results'
    file_name = 'mm10_negative_controls.csv'
    return send_from_directory(result_dir, file_name, as_attachment=True)


@main.route('/under_development')
def under_development():
    return render_template('under_development.html')
