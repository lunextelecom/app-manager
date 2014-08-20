'''
Created on Sep 10, 2010

@author: khoatran
'''
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os

def connect_to_server(host, port, username, password):
    server = smtplib.SMTP(host, port)
    #server.ehlo()
    #server.starttls()
    server.ehlo()
    server.login(username, password)

    return server

def send_mail(send_from, send_to, subject, text, server, files=[]):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(file,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    smtp = server
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

def send_mail_inv(send_from, send_to, subject, text, streams={}, server=None, cc = None):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    if cc:
        msg['Cc'] = cc

    msg.attach( MIMEText(text) )

    for fn,stream in streams.iteritems():
        part = MIMEBase('application', "octet-stream")
        part.set_payload( stream )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % (fn))
        msg.attach(part)

    smtp = server
    try:
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()
    except smtplib.SMTPServerDisconnected:
        smtp.connect()
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()

def send_email_ex(strFrom, strTo, title, plain_text, html, smtp_server, embedded_images={}, attachments=
    # Create the root message and fill in the from, to, and subject headers
    {}):
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = title
    msgRoot['From'] = strFrom #strTo = ['haonguyen@lunextelecom.com']
    msgRoot['To'] = COMMASPACE.join(strTo)
    msgRoot.preamble = 'This is a multi-part message in MIME format.'
    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)
    msgText = MIMEText(plain_text)
    msgAlternative.attach(msgText)
    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText(html, 'html')
    msgAlternative.attach(msgText)
#    for cid, fn in embedded_images.iteritems():
#        # This example assumes the image is in the current directory
#        fp = open(fn, 'rb')
#        msgImage = MIMEImage(fp.read())
#        fp.close() # Define the image's ID as referenced above
#        msgImage.add_header('Content-ID', '<%s>' % cid)
#        msgRoot.attach(msgImage)
    
    for fn, attachment in attachments.iteritems():
        part = MIMEBase('application', "octet-stream")
        part.set_payload(attachment)
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % (fn))
        msgRoot.attach(part)
    
    smtp = smtp_server
    try:
        smtp.sendmail(strFrom, strTo, msgRoot.as_string())
        smtp.quit()
    except smtplib.SMTPServerDisconnected:
        smtp.connect()
        smtp.sendmail(strFrom, strTo, msgRoot.as_string())
        smtp.quit()
    
def send_email_html(send_from, send_to, subject, text, server, embedded_images = {}, attachments = {}):   
    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subject
    msgRoot['From'] = send_from
    msgRoot['To'] = COMMASPACE.join(send_to)
    msgRoot.preamble = 'This is a multi-part message in MIME format.'
    
    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)
    
#    msgText = MIMEText(text_content)
#    msgAlternative.attach(msgText)
    
    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText(text, 'html')
    msgAlternative.attach(msgText)
    
    for cid,fn in embedded_images.iteritems():        
        # This example assumes the image is in the current directory
        fp = open(fn, 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()        
        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<%s>' % cid)
        msgRoot.attach(msgImage)
        
    for fn,attachment in attachments.iteritems():
        part = MIMEBase('application', "octet-stream")
        part.set_payload( attachment )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % (fn))
        msgRoot.attach(part)
        
    smtp = server
    try:
        smtp.sendmail(send_from, send_to, msgRoot.as_string())
        smtp.quit()
    except smtplib.SMTPServerDisconnected:
        smtp.connect()
        smtp.sendmail(send_from, send_to, msgRoot.as_string())
        smtp.quit()
        
def send_email_cc_html(send_from, send_to, subject, text, server, cc=[], embedded_images = {}, attachments = {}):   
    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subject
    msgRoot['From'] = '; '.join(send_from)
    msgRoot['To'] = '; '.join(send_to)#COMMASPACE.join(send_to)
    msgRoot['Cc'] = '; '.join(cc)#COMMASPACE.join(send_to)
    msgRoot.preamble = 'This is a multi-part message in MIME format.'
    send_to = send_to + cc
    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)
    
#    msgText = MIMEText(text_content)
#    msgAlternative.attach(msgText)
    
    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText(text, 'html')
    msgAlternative.attach(msgText)
    
    for cid,fn in embedded_images.iteritems():        
        # This example assumes the image is in the current directory
        fp = open(fn, 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()        
        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<%s>' % cid)
        msgRoot.attach(msgImage)
        
    for fn,attachment in attachments.iteritems():
        part = MIMEBase('application', "octet-stream")
        part.set_payload( attachment )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % (fn))
        msgRoot.attach(part)
        
    smtp = server
    try:
        smtp.sendmail(send_from, send_to, msgRoot.as_string())
        smtp.quit()
    except smtplib.SMTPServerDisconnected:
        smtp.connect()
        smtp.sendmail(send_from, send_to, msgRoot.as_string())
        smtp.quit()
    
def send_email(send_from, send_to, subject, text, 
               server, streams={}, cc=None):
    
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    if cc:
        msg['Cc'] = cc

    msg.attach( MIMEText(text) )

    for fn,stream in streams.iteritems():
        part = MIMEBase('application', "octet-stream")
        part.set_payload( stream )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % (fn))
        msg.attach(part)
            
    smtp = server
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()